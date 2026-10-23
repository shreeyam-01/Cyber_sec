import os
import sys
import json
import random
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

# Re-use our modular components
from dataset import sanitize_code
from static_analyzer import StaticFeatureExtractor
from llm_encoder import LLMFeatureEncoder
from fusion_model import LLMEnhancedStaticClassifier
from evaluate import compute_metrics, print_evaluation_report

CONFIG_PHASE2 = {
    "dataset_path": r"D:\cybersec_2\phase2_dataset\phase2_dataset.json",
    "llm_model_id": "Qwen/Qwen2.5-Coder-0.5B-Instruct",
    "max_seq_len": 256,
    "batch_size": 32,
    "epochs": 15,
    "learning_rate": 0.001,
    "weight_decay": 0.01,
    "hidden_dim": 256,
    "static_feat_dim": 48,
    "dropout": 0.3,
    "seed": 42,
    "results_dir": r"D:\cybersec_2\phase2_results",
    "checkpoints_dir": r"D:\cybersec_2\phase2_checkpoints"
}

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def extract_split_samples(raw_data, split_name):
    records = [r for r in raw_data if r['split'] == split_name]
    texts, labels, cwes, func_ids = [], [], [], []
    for r in records:
        vuln_clean = sanitize_code(r['code_vulnerable'])
        texts.append(vuln_clean)
        labels.append(1)
        cwes.append(r['cwe_class'])
        func_ids.append(r['function_id'] + "_vuln")
        if r['code_fixed'] is not None:
            fixed_clean = sanitize_code(r['code_fixed'])
            texts.append(fixed_clean)
            labels.append(0)
            cwes.append(r['cwe_class'])
            func_ids.append(r['function_id'] + "_fixed")
    return texts, labels, cwes, func_ids

def main():
    print("=" * 70)
    print("PHASE 2 TRAINING & EVALUATION PIPELINE")
    print("69 Seen CWEs (Train/Val/Seen-Test) vs 20 Held-Out Unseen CWEs")
    print("=" * 70)

    set_seed(CONFIG_PHASE2["seed"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # 1. Load Dataset
    with open(CONFIG_PHASE2["dataset_path"], "r", encoding="utf-8") as f:
        data = json.load(f)

    train_texts, train_labels, train_cwes, train_ids = extract_split_samples(data, "train")
    val_texts, val_labels, val_cwes, val_ids = extract_split_samples(data, "val")
    seen_texts, seen_labels, seen_cwes, seen_ids = extract_split_samples(data, "test_seen")
    held_texts, held_labels, held_cwes, held_ids = extract_split_samples(data, "test_held_out")

    print(f"  Train samples:     {len(train_labels)} (Vuln: {sum(train_labels)}, Safe: {len(train_labels)-sum(train_labels)})")
    print(f"  Val samples:       {len(val_labels)} (Vuln: {sum(val_labels)}, Safe: {len(val_labels)-sum(val_labels)})")
    print(f"  Seen Test:         {len(seen_labels)} (Vuln: {sum(seen_labels)}, Safe: {len(seen_labels)-sum(seen_labels)})")
    print(f"  Held-out Test:     {len(held_labels)} (Vuln: {sum(held_labels)}, Safe: {len(held_labels)-sum(held_labels)})")

    # 2. Extract Static Features
    print("\n[Step 1/4] Extracting Static Features (48-D)...")
    analyzer = StaticFeatureExtractor()
    static_cache_dir = os.path.join(CONFIG_PHASE2["checkpoints_dir"], "static_cache")
    os.makedirs(static_cache_dir, exist_ok=True)

    def get_static(texts, split):
        path = os.path.join(static_cache_dir, f"static_{split}.npy")
        if os.path.exists(path):
            return np.load(path)
        print(f"  Extracting {split} static features ({len(texts)} samples)...")
        feats = analyzer.extract_features_batch(texts)
        np.save(path, feats)
        return feats

    X_st_train = torch.tensor(get_static(train_texts, "train"), dtype=torch.float32)
    X_st_val = torch.tensor(get_static(val_texts, "val"), dtype=torch.float32)
    X_st_seen = torch.tensor(get_static(seen_texts, "seen"), dtype=torch.float32)
    X_st_held = torch.tensor(get_static(held_texts, "held_out"), dtype=torch.float32)

    # 3. Extract LLM Embeddings
    print("\n[Step 2/4] Extracting LLM Semantic Embeddings (Qwen2.5-Coder-0.5B)...")
    llm_encoder = LLMFeatureEncoder(
        model_id=CONFIG_PHASE2["llm_model_id"],
        device="cuda" if torch.cuda.is_available() else "cpu",
        max_len=CONFIG_PHASE2["max_seq_len"]
    )
    emb_cache_dir = os.path.join(CONFIG_PHASE2["checkpoints_dir"], "llm_embeddings")
    os.makedirs(emb_cache_dir, exist_ok=True)

    X_llm_train = llm_encoder.extract_or_load_embeddings(
        train_texts, os.path.join(emb_cache_dir, "llm_train.pt"), batch_size=CONFIG_PHASE2["batch_size"]
    )
    X_llm_val = llm_encoder.extract_or_load_embeddings(
        val_texts, os.path.join(emb_cache_dir, "llm_val.pt"), batch_size=CONFIG_PHASE2["batch_size"]
    )
    X_llm_seen = llm_encoder.extract_or_load_embeddings(
        seen_texts, os.path.join(emb_cache_dir, "llm_seen.pt"), batch_size=CONFIG_PHASE2["batch_size"]
    )
    X_llm_held = llm_encoder.extract_or_load_embeddings(
        held_texts, os.path.join(emb_cache_dir, "llm_held_out.pt"), batch_size=CONFIG_PHASE2["batch_size"]
    )

    del llm_encoder.model
    torch.cuda.empty_cache() if torch.cuda.is_available() else None

    # 4. Train GCFN
    print("\n[Step 3/4] Training Gated Cross-Modality Fusion Network on 69 Seen CWEs...")
    y_train = torch.tensor(train_labels, dtype=torch.float32)
    y_val = torch.tensor(val_labels, dtype=torch.float32)

    train_ds = TensorDataset(X_st_train, X_llm_train, y_train)
    val_ds = TensorDataset(X_st_val, X_llm_val, y_val)
    train_loader = DataLoader(train_ds, batch_size=CONFIG_PHASE2["batch_size"], shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=CONFIG_PHASE2["batch_size"], shuffle=False)

    model = LLMEnhancedStaticClassifier(
        static_dim=CONFIG_PHASE2["static_feat_dim"],
        llm_dim=X_llm_train.shape[1],
        hidden_dim=CONFIG_PHASE2["hidden_dim"],
        dropout=CONFIG_PHASE2["dropout"]
    ).to(device)

    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=CONFIG_PHASE2["learning_rate"], weight_decay=CONFIG_PHASE2["weight_decay"])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=CONFIG_PHASE2["epochs"])

    best_val_f1 = 0.0
    best_threshold = 0.5
    best_state = None

    for epoch in range(1, CONFIG_PHASE2["epochs"] + 1):
        model.train()
        total_loss = 0.0
        for b_st, b_llm, b_y in train_loader:
            b_st, b_llm, b_y = b_st.to(device), b_llm.to(device), b_y.to(device)
            optimizer.zero_grad()
            logits = model(b_st, b_llm)
            loss = criterion(logits, b_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        scheduler.step()
        avg_loss = total_loss / len(train_loader)

        # Validation tuning
        model.eval()
        val_probs = []
        with torch.no_grad():
            for b_st, b_llm, _ in val_loader:
                b_st, b_llm = b_st.to(device), b_llm.to(device)
                logits = model(b_st, b_llm)
                val_probs.extend(torch.sigmoid(logits).cpu().numpy())

        val_probs = np.array(val_probs)
        best_ep_f1, best_ep_thresh = 0.0, 0.5
        for t in np.arange(0.3, 0.75, 0.05):
            t_preds = (val_probs >= t).astype(int)
            tp = np.sum((t_preds == 1) & (np.array(val_labels) == 1))
            fp = np.sum((t_preds == 1) & (np.array(val_labels) == 0))
            fn = np.sum((t_preds == 0) & (np.array(val_labels) == 1))
            p = tp / (tp + fp) if (tp + fp) > 0 else 0
            r = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = (2 * p * r / (p + r)) if (p + r) > 0 else 0
            if f1 > best_ep_f1:
                best_ep_f1, best_ep_thresh = f1, t

        print(f"  Epoch {epoch:02d}/{CONFIG_PHASE2['epochs']} | Loss: {avg_loss:.4f} | Val F1: {best_ep_f1*100:.2f}% (thresh: {best_ep_thresh:.2f})")

        if best_ep_f1 > best_val_f1:
            best_val_f1 = best_ep_f1
            best_threshold = best_ep_thresh
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    print(f"\nTraining Complete. Best Validation F1: {best_val_f1*100:.2f}% at threshold: {best_threshold:.2f}")
    model.load_state_dict(best_state)
    model = model.to(device)
    torch.save(best_state, os.path.join(CONFIG_PHASE2["checkpoints_dir"], "best_phase2_model.pt"))

    # 5. Evaluate
    print("\n[Step 4/4] Evaluating on 69 Seen Test CWEs and 20 Held-Out Unseen CWEs...")
    def predict_split(X_st, X_llm, thresh):
        model.eval()
        ds = TensorDataset(X_st, X_llm)
        loader = DataLoader(ds, batch_size=CONFIG_PHASE2["batch_size"], shuffle=False)
        all_probs = []
        with torch.no_grad():
            for b_st, b_llm in loader:
                b_st, b_llm = b_st.to(device), b_llm.to(device)
                logits = model(b_st, b_llm)
                all_probs.extend(torch.sigmoid(logits).cpu().numpy())
        all_probs = np.array(all_probs)
        preds = (all_probs >= thresh).astype(int).tolist()
        return preds, all_probs.tolist()

    seen_preds, seen_probs = predict_split(X_st_seen, X_llm_seen, best_threshold)
    held_preds, held_probs = predict_split(X_st_held, X_llm_held, best_threshold)

    seen_metrics = compute_metrics(seen_labels, seen_preds, seen_probs, seen_cwes)
    held_metrics = compute_metrics(held_labels, held_preds, held_probs, held_cwes)

    print_evaluation_report("Phase 2 - Test Seen (69 CWEs)", seen_metrics)
    print_evaluation_report("Phase 2 - Test Unseen (20 Held-Out CWEs)", held_metrics)

    results_payload = {
        "framework": "Phase 2 LLM-Enhanced Static Analysis (69 Seen vs 20 Unseen CWEs)",
        "tuning_threshold": round(float(best_threshold), 2),
        "validation_f1": round(float(best_val_f1 * 100), 2),
        "test_seen": seen_metrics,
        "test_unseen": held_metrics
    }
    out_res = os.path.join(CONFIG_PHASE2["results_dir"], "phase2_results.json")
    with open(out_res, "w") as f:
        json.dump(results_payload, f, indent=2)
    print(f"\nPhase 2 results saved to: {out_res}")

if __name__ == "__main__":
    main()
