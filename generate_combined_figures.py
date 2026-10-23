import os
import json
import numpy as np
import matplotlib.pyplot as plt

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 0.8

P1_RES_PATH = r"D:\cybersec_2\results\llm_static_framework_results.json"
P2_RES_PATH = r"D:\cybersec_2\phase2_results\phase2_results.json"

OUT_DIRS = [
    r"D:\cybersec_2\combined_figures",
    os.path.join(os.path.expanduser('~'), 'OneDrive', 'Desktop', 'combined_figures')
]

for d in OUT_DIRS:
    os.makedirs(d, exist_ok=True)

with open(P1_RES_PATH, 'r') as f:
    p1 = json.load(f)
with open(P2_RES_PATH, 'r') as f:
    p2 = json.load(f)

# Aggregate Seen
s_tp = p1["test_seen"]["tp"] + p2["test_seen"]["tp"]
s_fp = p1["test_seen"]["fp"] + p2["test_seen"]["fp"]
s_fn = p1["test_seen"]["fn"] + p2["test_seen"]["fn"]
s_tn = p1["test_seen"]["tn"] + p2["test_seen"]["tn"]

s_rec = (s_tp / (s_tp + s_fn)) * 100
s_prec = (s_tp / (s_tp + s_fp)) * 100
s_f1 = (2 * s_prec * s_rec / (s_prec + s_rec)) if (s_prec + s_rec) > 0 else 0
s_fpr = (s_fp / (s_fp + s_tn)) * 100
s_acc = ((s_tp + s_tn) / (s_tp + s_tn + s_fp + s_fn)) * 100

# Aggregate Unseen
u_tp = p1["test_unseen"]["tp"] + p2["test_unseen"]["tp"]
u_fp = p1["test_unseen"]["fp"] + p2["test_unseen"]["fp"]
u_fn = p1["test_unseen"]["fn"] + p2["test_unseen"]["fn"]
u_tn = p1["test_unseen"]["tn"] + p2["test_unseen"]["tn"]

u_rec = (u_tp / (u_tp + u_fn)) * 100
u_prec = (u_tp / (u_tp + u_fp)) * 100
u_f1 = (2 * u_prec * u_rec / (u_prec + u_rec)) if (u_prec + u_rec) > 0 else 0
u_fpr = (u_fp / (u_fp + u_tn)) * 100
u_acc = ((u_tp + u_tn) / (u_tp + u_tn + u_fp + u_fn)) * 100

# -------------------------------------------------------------------------
# 1. Confusion Matrix (Phase 1 + Phase 2 Combined)
# -------------------------------------------------------------------------
def generate_combined_confusion():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=300)

    cm_seen = np.array([[s_tn, s_fp], [s_fn, s_tp]])
    cm_unseen = np.array([[u_tn, u_fp], [u_fn, u_tp]])

    panels = [
        (cm_seen, f'Combined: Seen Test Sets (84 CWEs, N = {s_tp+s_fp+s_fn+s_tn:,})', axes[0], plt.cm.Blues),
        (cm_unseen, f'Combined: Unseen Held-Out Test Sets (25 CWEs, N = {u_tp+u_fp+u_fn+u_tn:,})', axes[1], plt.cm.Purples)
    ]

    for cm, title, ax, cmap in panels:
        ax.imshow(cm, interpolation='nearest', cmap=cmap)
        ax.set_title(title, fontsize=11.5, fontweight='bold', pad=12)
        ticks = np.arange(2)
        ax.set_xticks(ticks)
        ax.set_xticklabels(['Safe (0)', 'Vulnerable (1)'], fontsize=10)
        ax.set_yticks(ticks)
        ax.set_yticklabels(['Safe (0)', 'Vulnerable (1)'], fontsize=10)

        thresh = cm.max() / 2.0
        labels = [['TN', 'FP'], ['FN', 'TP']]
        for i in range(2):
            for j in range(2):
                val = cm[i, j]
                tag = labels[i][j]
                ax.text(j, i, f"{val:,}\n({tag})",
                        ha="center", va="center",
                        color="white" if val > thresh else "black",
                        fontsize=12, fontweight='bold')

        ax.set_ylabel('True Label', fontsize=11, fontweight='bold')
        ax.set_xlabel('Predicted Label', fontsize=11, fontweight='bold')
        ax.grid(False)

    plt.tight_layout()
    for d in OUT_DIRS:
        p = os.path.join(d, "confusion_matrices_combined_phase1_2.png")
        plt.savefig(p, dpi=300, bbox_inches='tight')
    plt.close()
    print("[Combined] Confusion Matrix saved.")

# -------------------------------------------------------------------------
# 2. Comparative Benchmarks (Seen vs Unseen of Phase 1 + Phase 2)
# -------------------------------------------------------------------------
def generate_combined_benchmarks():
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)

    categories = ['Recall (%)', 'Precision (%)', 'F1-Score (%)', 'False Positive Rate (%)', 'Accuracy (%)']
    seen_scores = [s_rec, s_prec, s_f1, s_fpr, s_acc]
    unseen_scores = [u_rec, u_prec, u_f1, u_fpr, u_acc]

    x = np.arange(len(categories))
    width = 0.35

    b1 = ax.bar(x - width/2, seen_scores, width, label='Combined Seen Categories (84 CWEs)', color='#1d4ed8', edgecolor='#1e3a8a', alpha=0.9)
    b2 = ax.bar(x + width/2, unseen_scores, width, label='Combined Unseen Categories (25 CWEs)', color='#7c3aed', edgecolor='#5b21b6', alpha=0.9)

    for bars in [b1, b2]:
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f'{h:.2f}%',
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    ax.set_title('Combined (Phase 1 + 2): Comparative Benchmarks Across Seen & Unseen CWEs', fontsize=12.5, fontweight='bold', pad=14)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=10, fontweight='bold')
    ax.set_ylabel('Percentage (%)', fontsize=11, fontweight='bold')
    ax.set_ylim(0, 115)
    ax.legend(loc='upper right', frameon=True, fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    for d in OUT_DIRS:
        p = os.path.join(d, "comparative_benchmarks_combined_phase1_2.png")
        plt.savefig(p, dpi=300, bbox_inches='tight')
    plt.close()
    print("[Combined] Comparative Benchmark saved.")

# -------------------------------------------------------------------------
# 3. Detailed Generalization Breakdown (All 25 Held-Out CWEs of Phase 1 + Phase 2)
# -------------------------------------------------------------------------
def generate_combined_unseen_breakdown():
    # Merge the 5 P1 unseen CWEs with the 20 P2 unseen CWEs
    combined_cwes_dict = {}
    for cwe, stats in p1["test_unseen"]["cwe_stats"].items():
        combined_cwes_dict[f"{cwe} (P1)"] = stats
    for cwe, stats in p2["test_unseen"]["cwe_stats"].items():
        combined_cwes_dict[f"{cwe} (P2)"] = stats

    cwes = sorted(combined_cwes_dict.keys())
    recalls = [combined_cwes_dict[c]["recall"] for c in cwes]
    precisions = [combined_cwes_dict[c]["precision"] for c in cwes]
    f1s = [combined_cwes_dict[c]["f1"] for c in cwes]
    fprs = [combined_cwes_dict[c]["fpr"] for c in cwes]

    fig, ax = plt.subplots(figsize=(19, 7), dpi=300)
    x = np.arange(len(cwes))
    width = 0.2

    b1 = ax.bar(x - 1.5*width, recalls, width, label='Recall (%)', color='#3b82f6')
    b2 = ax.bar(x - 0.5*width, precisions, width, label='Precision (%)', color='#10b981')
    b3 = ax.bar(x + 0.5*width, f1s, width, label='F1-Score (%)', color='#f59e0b')
    b4 = ax.bar(x + 1.5*width, fprs, width, label='False Positive Rate (%) [Lower is Better]', color='#ef4444')

    ax.set_title('Combined (Phase 1 + 2): Generalization Breakdown Across All 25 Held-Out (Unseen) CWE Categories', fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(cwes, fontsize=9, fontweight='bold', rotation=45, ha='right')
    ax.set_ylabel('Percentage (%)', fontsize=11, fontweight='bold')
    ax.set_ylim(0, 115)
    ax.legend(loc='lower right', frameon=True, fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    for d in OUT_DIRS:
        p = os.path.join(d, "unseen_cwe_breakdown_combined_phase1_2.png")
        plt.savefig(p, dpi=300, bbox_inches='tight')
    plt.close()
    print("[Combined] Detailed Generalization Breakdown saved.")

if __name__ == "__main__":
    generate_combined_confusion()
    generate_combined_benchmarks()
    generate_combined_unseen_breakdown()
    print("Done Combined figures.")
