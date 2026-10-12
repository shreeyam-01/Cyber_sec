import os
import sys
import json
import random
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

from dataset import JulietDataset
from static_analyzer import StaticFeatureExtractor
from llm_encoder import LLMFeatureEncoder
from fusion_model import LLMEnhancedStaticClassifier
from evaluate import compute_metrics, print_evaluation_report

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def main():
    print("=" * 70)
    print("LLM-ENHANCED STATIC ANALYSIS FRAMEWORK")
    print("Vulnerability Detection & Unseen CWE Generalization")
    print("=" * 70)
    
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
        
    set_seed(config["seed"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Execution Device: {device}")
    
    # 1. Dataset Loading
    dataset = JulietDataset(config["dataset_path"])
    
    print("\n[Step 1/5] Extracting sanitized code splits...")
    train_texts, train_labels, train_cwes, train_ids = dataset.get_split_samples("train")
    val_texts, val_labels, val_cwes, val_ids = dataset.get_split_samples("val")
    seen_texts, seen_labels, seen_cwes, seen_ids = dataset.get_split_samples("test_seen")
    held_texts, held_labels, held_cwes, held_ids = dataset.get_split_samples("test_held_out")
    
    print(f"  Train samples: {len(train_labels)} (Vuln: {sum(train_labels)}, Safe: {len(train_labels)-sum(train_labels)})")
    print(f"  Val samples:   {len(val_labels)} (Vuln: {sum(val_labels)}, Safe: {len(val_labels)-sum(val_labels)})")
    print(f"  Seen test:     {len(seen_labels)} (Vuln: {sum(seen_labels)}, Safe: {len(seen_labels)-sum(seen_labels)})")
    print(f"  Held-out test: {len(held_labels)} (Vuln: {sum(held_labels)}, Safe: {len(held_labels)-sum(held_labels)})")

    # 2. Static Analysis Feature Extraction
    print("\n[Step 2/5] Extracting static analysis domain features...")
    analyzer = StaticFeatureExtractor()
    
    static_cache_dir = os.path.join(config["checkpoints_dir"], "static_cache")
    os.makedirs(static_cache_dir, exist_ok=True)
    
    def get_static_features(texts, split_name):
        cache_path = os.path.join(static_cache_dir, f"static_{split_name}.npy")
        if os.path.exists(cache_path):
            print(f"  Loading static features from {cache_path}")
            return np.load(cache_path)
        print(f"  Computing static features for {split_name} ({len(texts)} samples)...")
        feats = analyzer.extract_features_batch(texts)
        np.save(cache_path, feats)
        return feats

    X_static_train = torch.tensor(get_static_features(train_texts, "train"), dtype=torch.float32)
    X_static_val = torch.tensor(get_static_features(val_texts, "val"), dtype=torch.float32)
    X_static_seen = torch.tensor(get_static_features(seen_texts, "seen"), dtype=torch.float32)
    X_static_held = torch.tensor(get_static_features(held_texts, "held_out"), dtype=torch.float32)

    # 3. LLM Semantic Feature Extraction
    print("\n[Step 3/5] Extracting LLM semantic representations (Qwen2.5-Coder-0.5B)...")
    llm_encoder = LLMFeatureEncoder(
        model_id=config["llm_model_id"],
        device="cuda" if torch.cuda.is_available() else "cpu",
        max_len=config["max_seq_len"]
    )
    
    emb_cache_dir = os.path.join(config["checkpoints_dir"], "llm_embeddings")
    os.makedirs(emb_cache_dir, exist_ok=True)
    
    X_llm_train = llm_encoder.extract_or_load_embeddings(
        train_texts, os.path.join(emb_cache_dir, "llm_train.pt"), batch_size=config["batch_size"]
    )
    X_llm_val = llm_encoder.extract_or_load_embeddings(
        val_texts, os.path.join(emb_cache_dir, "llm_val.pt"), batch_size=config["batch_size"]
    )
    X_llm_seen = llm_encoder.extract_or_load_embeddings(
        seen_texts, os.path.join(emb_cache_dir, "llm_seen.pt"), batch_size=config["batch_size"]
    )
    X_llm_held = llm_encoder.extract_or_load_embeddings(
        held_texts, os.path.join(emb_cache_dir, "llm_held_out.pt"), batch_size=config["batch_size"]
    )

    # Free LLM backbone memory on GPU before training fusion network
    del llm_encoder.model
    torch.cuda.empty_cache() if torch.cuda.is_available() else None

    # 4. Training Gated Fusion Network
    print("\n[Step 4/5] Training Gated Cross-Modality Fusion Network on training split only...")
    y_train = torch.tensor(train_labels, dtype=torch.float32)
    y_val = torch.tensor(val_labels, dtype=torch.float32)

    train_ds = TensorDataset(X_static_train, X_llm_train, y_train)
    val_ds = TensorDataset(X_static_val, X_llm_val, y_val)

    train_loader = DataLoader(train_ds, batch_size=config["batch_size"], shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=config["batch_size"], shuffle=False)

    model = LLMEnhancedStaticClassifier(
        static_dim=config["static_feat_dim"],
        llm_dim=X_llm_train.shape[1],
        hidden_dim=config["hidden_dim"],
        dropout=config["dropout"]
    ).to(device)

    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config["learning_rate"],
        weight_decay=config["weight_decay"]
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config["epochs"])

    best_val_f1 = 0.0
    best_threshold = 0.5
    best_model_state = None

    for epoch in range(1, config["epochs"] + 1):
        model.train()
        total_loss = 0.0
        for b_static, b_llm, b_y in train_loader:
            b_static, b_llm, b_y = b_static.to(device), b_llm.to(device), b_y.to(device)
            optimizer.zero_grad()
            logits = model(b_static, b_llm)
            loss = criterion(logits, b_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        scheduler.step()
        avg_loss = total_loss / len(train_loader)

        # Validation tuning (strictly on validation set, NEVER held-out test)
        model.eval()
        val_probs = []
        with torch.no_grad():
            for b_static, b_llm, _ in val_loader:
                b_static, b_llm = b_static.to(device), b_llm.to(device)
                logits = model(b_static, b_llm)
                probs = torch.sigmoid(logits).cpu().numpy()
                val_probs.extend(probs)

        val_probs = np.array(val_probs)
        # Scan threshold on validation set to optimize F1
        best_ep_f1 = 0.0
        best_ep_thresh = 0.5
        for t in np.arange(0.3, 0.75, 0.05):
            t_preds = (val_probs >= t).astype(int)
            tp = np.sum((t_preds == 1) & (np.array(val_labels) == 1))
            fp = np.sum((t_preds == 1) & (np.array(val_labels) == 0))
            fn = np.sum((t_preds == 0) & (np.array(val_labels) == 1))
            p = tp / (tp + fp) if (tp + fp) > 0 else 0
            r = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = (2 * p * r / (p + r)) if (p + r) > 0 else 0
            if f1 > best_ep_f1:
                best_ep_f1 = f1
                best_ep_thresh = t

        print(f"  Epoch {epoch:02d}/{config['epochs']} | Loss: {avg_loss:.4f} | Val F1: {best_ep_f1*100:.2f}% (thresh: {best_ep_thresh:.2f})")

        if best_ep_f1 > best_val_f1:
            best_val_f1 = best_ep_f1
            best_threshold = best_ep_thresh
            best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    print(f"\nTraining Complete. Best Validation F1: {best_val_f1*100:.2f}% at threshold: {best_threshold:.2f}")
    
    # Save best checkpoint
    model.load_state_dict(best_model_state)
    model = model.to(device)
    torch.save(best_model_state, os.path.join(config["checkpoints_dir"], "best_fusion_model.pt"))

    # 5. Independent Evaluation on Seen and Unseen Test Splits
    print("\n[Step 5/5] Evaluating on Test Seen and Test Held-Out (Unseen CWE) splits...")
    
    def predict_split(X_static, X_llm, threshold):
        model.eval()
        ds = TensorDataset(X_static, X_llm)
        loader = DataLoader(ds, batch_size=config["batch_size"], shuffle=False)
        all_probs = []
        with torch.no_grad():
            for b_static, b_llm in loader:
                b_static, b_llm = b_static.to(device), b_llm.to(device)
                logits = model(b_static, b_llm)
                probs = torch.sigmoid(logits).cpu().numpy()
                all_probs.extend(probs)
        all_probs = np.array(all_probs)
        preds = (all_probs >= threshold).astype(int).tolist()
        return preds, all_probs.tolist()

    seen_preds, seen_probs = predict_split(X_static_seen, X_llm_seen, best_threshold)
    held_preds, held_probs = predict_split(X_static_held, X_llm_held, best_threshold)

    seen_metrics = compute_metrics(seen_labels, seen_preds, seen_probs, seen_cwes)
    held_metrics = compute_metrics(held_labels, held_preds, held_probs, held_cwes)

    print_evaluation_report("Test Seen Cases", seen_metrics)
    print_evaluation_report("Test Unseen Cases (Held-Out CWEs)", held_metrics)

    # 6. Save Predictions and Results
    results_payload = {
        "framework": "LLM-Enhanced Static Analysis Framework (GCFN)",
        "backbone": config["llm_model_id"],
        "tuning_threshold": round(float(best_threshold), 2),
        "validation_f1": round(float(best_val_f1 * 100), 2),
        "test_seen": seen_metrics,
        "test_unseen": held_metrics
    }
    
    results_file = os.path.join(config["results_dir"], "llm_static_framework_results.json")
    with open(results_file, "w") as f:
        json.dump(results_payload, f, indent=2)
    print(f"Results saved to: {results_file}")

    # Save detailed per-sample predictions
    def save_predictions(filename, ids, cwes, y_true, preds, probs):
        records = []
        for i in range(len(ids)):
            records.append({
                "function_id": ids[i],
                "cwe": cwes[i],
                "label": y_true[i],
                "prediction": preds[i],
                "confidence": round(probs[i], 4)
            })
        with open(filename, "w") as f:
            json.dump(records, f, indent=2)

    save_predictions(
        os.path.join(config["results_dir"], "predictions_seen.json"),
        seen_ids, seen_cwes, seen_labels, seen_preds, seen_probs
    )
    save_predictions(
        os.path.join(config["results_dir"], "predictions_unseen.json"),
        held_ids, held_cwes, held_labels, held_preds, held_probs
    )

if __name__ == "__main__":
    main()
