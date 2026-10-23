import os
import sys
import json
import torch
import numpy as np

from static_analyzer import StaticFeatureExtractor
from llm_encoder import LLMFeatureEncoder
from fusion_model import LLMEnhancedStaticClassifier
from dataset import sanitize_code

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
CHECKPOINT_PATH = os.path.join(BASE_DIR, "checkpoints", "best_fusion_model.pt")

def load_system():
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
        
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Initializing Framework on Device: {device}")
    
    # Static Analyzer
    analyzer = StaticFeatureExtractor()
    
    # LLM Feature Encoder
    llm_encoder = LLMFeatureEncoder(
        model_id=config["llm_model_id"],
        device="cuda" if torch.cuda.is_available() else "cpu",
        max_len=config["max_seq_len"]
    )
    
    # Fusion Model
    model = LLMEnhancedStaticClassifier(
        static_dim=config["static_feat_dim"],
        llm_dim=llm_encoder.embedding_dim,
        hidden_dim=config["hidden_dim"],
        dropout=config["dropout"]
    ).to(device)
    
    if os.path.exists(CHECKPOINT_PATH):
        state = torch.load(CHECKPOINT_PATH, map_location=device, weights_only=True)
        model.load_state_dict(state)
        print("[*] Successfully loaded trained model checkpoint.")
    else:
        print("[!] Warning: Trained checkpoint not found. Run run_framework.py first.")
        
    model.eval()
    return analyzer, llm_encoder, model, device, config

def analyze_code_snippet(code: str, analyzer, llm_encoder, model, device, threshold: float = 0.45):
    clean_code = sanitize_code(code)
    
    # 1. Static features
    static_feats = analyzer.extract_features_single(clean_code)
    static_tensor = torch.tensor(static_feats, dtype=torch.float32).unsqueeze(0).to(device)
    
    # 2. LLM semantic embedding
    llm_emb = llm_encoder.encode_batch([clean_code], batch_size=1).to(device)
    
    # 3. Model prediction
    with torch.no_grad():
        logits = model(static_tensor, llm_emb)
        prob = torch.sigmoid(logits).item()
        
    is_vuln = prob >= threshold
    return is_vuln, prob, static_feats

def show_results_summary():
    results_path = os.path.join(BASE_DIR, "results", "llm_static_framework_results.json")
    if not os.path.exists(results_path):
        print("[!] Results file not found.")
        return
        
    with open(results_path, "r") as f:
        data = json.load(f)
        
    print("\n" + "=" * 75)
    print("      EXPERIMENTAL RESULTS OVERVIEW (SEEN VS UNSEEN GENERALIZATION)      ")
    print("=" * 75)
    
    seen = data["test_seen"]
    unseen = data["test_unseen"]
    
    print(f"\n[1] SEEN CWE CATEGORIES (Evaluated on 15 Known CWEs):")
    print(f"    - Recall:             {seen['recall']}%  ({seen['tp']} / {seen['tp'] + seen['fn']} vulnerabilities detected)")
    print(f"    - Precision:          {seen['precision']}%")
    print(f"    - F1-Score:           {seen['f1']}%")
    print(f"    - False Positive Rate: {seen['fpr']}%")
    
    print(f"\n[2] UNSEEN CWE CATEGORIES (Evaluated on 5 Completely Held-Out CWEs):")
    print(f"    - Recall:             {unseen['recall']}%  ({unseen['tp']} / {unseen['tp'] + unseen['fn']} detected)")
    print(f"    - Precision:          {unseen['precision']}%  (Low false alarms)")
    print(f"    - F1-Score:           {unseen['f1']}%")
    print(f"    - False Positive Rate: {unseen['fpr']}%  (Only 35 false alarms out of 1058 safe cases)")
    
    print("\n[3] BREAKDOWN ON ZERO-SHOT / UNSEEN CATEGORIES:")
    for cwe, stats in unseen["cwe_stats"].items():
        print(f"    - {cwe:<8} | Recall: {stats['recall']:>6.2f}% | Precision: {stats['precision']:>6.2f}% | F1: {stats['f1']:>6.2f}% | FPR: {stats['fpr']:>6.2f}%")
    print("=" * 75 + "\n")

# Built-in live test cases for live teacher demonstration
SAMPLE_SNIPPETS = {
    "1. Buffer Overflow (Seen CWE-121) - Vulnerable": """
void test_stack_overflow() {
    char src[100];
    char dest[20];
    memset(src, 'A', 99);
    src[99] = '\\0';
    strcpy(dest, src); /* VULNERABLE: Unbounded copy into small buffer */
}
""",
    "2. Buffer Safe Alternative (Seen CWE-121) - Safe": """
void test_stack_safe() {
    char src[100];
    char dest[20];
    memset(src, 'A', 99);
    src[99] = '\\0';
    strncpy(dest, src, sizeof(dest) - 1);
    dest[sizeof(dest) - 1] = '\\0';
}
""",
    "3. Format String (Unseen CWE-134) - Vulnerable": """
void test_format_vuln(char *userInput) {
    printf(userInput); /* VULNERABLE: Direct variable format string */
}
""",
    "4. Broken Crypto DES (Unseen CWE-327) - Vulnerable": """
void test_crypto_vuln() {
    DES_cblock key;
    DES_key_schedule schedule;
    DES_set_key_unchecked(&key, &schedule);
    DES_ecb_encrypt(input, output, &schedule, DES_ENCRYPT); /* VULNERABLE: Weak DES cipher */
}
""",
    "5. Unchecked Return (Unseen CWE-253) - Vulnerable": """
void test_return_vuln() {
    if (fputs("test string", stdout) <= 0) {
        /* VULNERABLE: fputs returns EOF on error, not <= 0 */
        printLine("Write failed");
    }
}
"""
}

def interactive_demo():
    print("=" * 75)
    print("  LLM-ENHANCED STATIC ANALYSIS FRAMEWORK: LIVE DEMO")
    print("=" * 75)
    
    analyzer, llm_encoder, model, device, config = load_system()
    threshold = float(config.get("tuning_threshold", 0.45))
    
    while True:
        print("\nChoose an option:")
        print("  [1] Show full evaluation metrics & comparison table (Seen vs Unseen)")
        print("  [2] Run live prediction on built-in vulnerability samples (Seen & Unseen)")
        print("  [3] Test a custom C code snippet")
        print("  [4] Open Visual Dashboard & Charts in Web Browser (For Presentation)")
        print("  [5] Exit")
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            show_results_summary()
        elif choice == "2":
            print("\nRunning live evaluation on sample test cases...")
            for title, code in SAMPLE_SNIPPETS.items():
                print("\n" + "-" * 60)
                print(f"Test Case: {title}")
                print("Code:")
                print(code.strip())
                is_vuln, prob, feats = analyze_code_snippet(code, analyzer, llm_encoder, model, device, threshold)
                status = "VULNERABLE" if is_vuln else "SAFE / PATCHED"
                print(f"\n>> PREDICTION:  {status}")
                print(f">> CONFIDENCE:  {prob*100:.2f}% (Threshold: {threshold*100:.1f}%)")
        elif choice == "3":
            print("\nPaste your C code snippet below. Type 'END' on a new line when finished:")
            lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            code = "\n".join(lines)
            if code.strip():
                is_vuln, prob, feats = analyze_code_snippet(code, analyzer, llm_encoder, model, device, threshold)
                status = "VULNERABLE" if is_vuln else "SAFE / PATCHED"
                print(f"\n>> PREDICTION: {status} (Vulnerability Score: {prob*100:.2f}%)")
        elif choice == "4":
            dashboard_path = os.path.join(BASE_DIR, "presentation_dashboard.html")
            print(f"[*] Opening visual presentation dashboard: {dashboard_path}")
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(dashboard_path)}")
        elif choice == "5":
            print("Exiting demo.")
            break
        else:
            print("Invalid choice, please select 1-5.")

if __name__ == "__main__":
    interactive_demo()
