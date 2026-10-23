import os
import json
import numpy as np
import matplotlib.pyplot as plt

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 0.8

P2_RES_PATH = r"D:\cybersec_2\phase2_results\phase2_results.json"
OUT_DIRS = [
    r"D:\cybersec_2\phase2_figures",
    os.path.join(os.path.expanduser('~'), 'OneDrive', 'Desktop', 'phase2_figures')
]

for d in OUT_DIRS:
    os.makedirs(d, exist_ok=True)

with open(P2_RES_PATH, 'r') as f:
    data = json.load(f)

seen = data["test_seen"]
unseen = data["test_unseen"]

# -------------------------------------------------------------------------
# 1. Confusion Matrix (Phase 2 Only)
# -------------------------------------------------------------------------
def generate_confusion_matrices():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=300)

    cm_seen = np.array([[seen["tn"], seen["fp"]], [seen["fn"], seen["tp"]]])
    cm_unseen = np.array([[unseen["tn"], unseen["fp"]], [unseen["fn"], unseen["tp"]]])

    panels = [
        (cm_seen, f'Phase 2: Seen Test Set (69 CWEs, N = {seen["tp"]+seen["fp"]+seen["fn"]+seen["tn"]:,})', axes[0], plt.cm.Blues),
        (cm_unseen, f'Phase 2: Unseen Held-Out Test Set (20 CWEs, N = {unseen["tp"]+unseen["fp"]+unseen["fn"]+unseen["tn"]:,})', axes[1], plt.cm.Purples)
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
        p = os.path.join(d, "confusion_matrices_phase2.png")
        plt.savefig(p, dpi=300, bbox_inches='tight')
    plt.close()
    print("[Phase 2] Confusion Matrix saved.")

# -------------------------------------------------------------------------
# 2. Comparative Benchmarks (Seen vs Unseen of Phase 2)
# -------------------------------------------------------------------------
def generate_benchmarks():
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)

    categories = ['Recall (%)', 'Precision (%)', 'F1-Score (%)', 'False Positive Rate (%)', 'Accuracy (%)']
    seen_scores = [seen["recall"], seen["precision"], seen["f1"], seen["fpr"], seen["accuracy"]]
    unseen_scores = [unseen["recall"], unseen["precision"], unseen["f1"], unseen["fpr"], unseen["accuracy"]]

    x = np.arange(len(categories))
    width = 0.35

    b1 = ax.bar(x - width/2, seen_scores, width, label='Seen Categories (69 CWEs)', color='#2563eb', edgecolor='#1e40af', alpha=0.9)
    b2 = ax.bar(x + width/2, unseen_scores, width, label='Unseen Held-Out Categories (20 CWEs)', color='#9333ea', edgecolor='#7e22ce', alpha=0.9)

    for bars in [b1, b2]:
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f'{h:.2f}%',
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    ax.set_title('Phase 2: Comparative Performance Benchmarks Across Seen & Unseen CWEs', fontsize=12.5, fontweight='bold', pad=14)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=10, fontweight='bold')
    ax.set_ylabel('Percentage (%)', fontsize=11, fontweight='bold')
    ax.set_ylim(0, 115)
    ax.legend(loc='upper right', frameon=True, fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    for d in OUT_DIRS:
        p = os.path.join(d, "comparative_benchmarks_phase2.png")
        plt.savefig(p, dpi=300, bbox_inches='tight')
    plt.close()
    print("[Phase 2] Comparative Benchmark saved.")

# -------------------------------------------------------------------------
# 3. Detailed Generalization Breakdown (20 Held-Out CWEs of Phase 2)
# -------------------------------------------------------------------------
def generate_unseen_breakdown():
    cwe_stats = unseen["cwe_stats"]
    cwes = sorted(cwe_stats.keys())

    recalls = [cwe_stats[c]["recall"] for c in cwes]
    precisions = [cwe_stats[c]["precision"] for c in cwes]
    f1s = [cwe_stats[c]["f1"] for c in cwes]
    fprs = [cwe_stats[c]["fpr"] for c in cwes]

    fig, ax = plt.subplots(figsize=(16, 6.5), dpi=300)
    x = np.arange(len(cwes))
    width = 0.2

    b1 = ax.bar(x - 1.5*width, recalls, width, label='Recall (%)', color='#3b82f6')
    b2 = ax.bar(x - 0.5*width, precisions, width, label='Precision (%)', color='#10b981')
    b3 = ax.bar(x + 0.5*width, f1s, width, label='F1-Score (%)', color='#f59e0b')
    b4 = ax.bar(x + 1.5*width, fprs, width, label='False Positive Rate (%) [Lower is Better]', color='#ef4444')

    ax.set_title('Phase 2: Generalization Breakdown Across All 20 Held-Out (Unseen) CWE Categories', fontsize=13.5, fontweight='bold', pad=14)
    ax.set_xticks(x)
    ax.set_xticklabels(cwes, fontsize=9.5, fontweight='bold', rotation=35, ha='right')
    ax.set_ylabel('Percentage (%)', fontsize=11, fontweight='bold')
    ax.set_ylim(0, 115)
    ax.legend(loc='lower right', frameon=True, fontsize=9.5)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    for d in OUT_DIRS:
        p = os.path.join(d, "unseen_cwe_breakdown_phase2.png")
        plt.savefig(p, dpi=300, bbox_inches='tight')
    plt.close()
    print("[Phase 2] Detailed Generalization Breakdown saved.")

if __name__ == "__main__":
    generate_confusion_matrices()
    generate_benchmarks()
    generate_unseen_breakdown()
    print("Done Phase 2 figures.")
