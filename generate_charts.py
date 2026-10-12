import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set professional styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

FIGURES_DIR = r"D:\cybersec_2\results\figures"
os.makedirs(FIGURES_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. CHART: BASELINE COMPARISON (SEEN VS UNSEEN)
# -------------------------------------------------------------
def plot_baseline_comparison():
    models = ['SVM', 'Random Forest', 'XGBoost', 'Proposed LLM-Static (GCFN)']
    
    # Seen Metrics
    seen_recall = [96.35, 94.11, 99.06, 99.65]
    seen_prec   = [86.47, 89.67, 86.61, 87.58]
    seen_f1     = [91.14, 91.84, 92.42, 93.22]
    seen_fpr    = [15.08, 10.84, 15.31, 14.13]
    
    # Unseen Metrics
    unseen_recall = [50.38, 90.36, 83.84, 80.06]
    unseen_prec   = [83.67, 94.19, 92.49, 96.03]
    unseen_f1     = [62.89, 92.23, 87.95, 87.32]
    unseen_fpr    = [9.83,   5.58,  6.81,  3.31]

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)
    
    x = np.arange(len(models))
    width = 0.2
    
    colors = ['#2b5c8f', '#2a9d8f', '#e76f51', '#7209b7']

    # Subplot 1: Seen Cases
    axes[0].bar(x - 1.5*width, seen_recall, width, label='Recall (%)', color='#3a86ff')
    axes[0].bar(x - 0.5*width, seen_prec,   width, label='Precision (%)', color='#38b000')
    axes[0].bar(x + 0.5*width, seen_f1,     width, label='F1-Score (%)', color='#ffb703')
    axes[0].bar(x + 1.5*width, seen_fpr,    width, label='FPR (%) [Lower is Better]', color='#e63946')
    
    axes[0].set_title('Performance on Seen CWE Categories (15 Known CWEs)', fontsize=13, fontweight='bold', pad=12)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(models, fontsize=9, fontweight='semibold')
    axes[0].set_ylabel('Percentage (%)', fontsize=11, fontweight='bold')
    axes[0].set_ylim(0, 110)
    axes[0].legend(loc='upper right', frameon=True)
    axes[0].grid(axis='y', linestyle='--', alpha=0.5)

    # Subplot 2: Unseen Cases
    axes[1].bar(x - 1.5*width, unseen_recall, width, label='Recall (%)', color='#3a86ff')
    axes[1].bar(x - 0.5*width, unseen_prec,   width, label='Precision (%)', color='#38b000')
    axes[1].bar(x + 0.5*width, unseen_f1,     width, label='F1-Score (%)', color='#ffb703')
    axes[1].bar(x + 1.5*width, unseen_fpr,    width, label='FPR (%) [Lower is Better]', color='#e63946')
    
    axes[1].set_title('Performance on Unseen CWE Categories (5 Held-Out CWEs)', fontsize=13, fontweight='bold', pad=12)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(models, fontsize=9, fontweight='semibold')
    axes[1].legend(loc='upper right', frameon=True)
    axes[1].grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    save_path = os.path.join(FIGURES_DIR, "baseline_comparison.png")
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[Chart] Saved: {save_path}")

# -------------------------------------------------------------
# 2. CHART: UNSEEN CWE BREAKDOWN
# -------------------------------------------------------------
def plot_unseen_breakdown():
    cwes = ['CWE-123\n(Write-What-Where)', 'CWE-134\n(Format String)', 'CWE-188\n(Memory Layout)', 'CWE-253\n(Unchecked Return)', 'CWE-327\n(Broken Crypto)']
    recall = [74.40, 88.25, 100.00, 72.00, 83.33]
    precision = [85.62, 96.19, 100.00, 100.00, 100.00]
    f1 = [79.62, 92.05, 100.00, 83.72, 90.91]
    fpr = [12.50, 3.50, 0.00, 0.00, 0.00]

    fig, ax = plt.subplots(figsize=(13, 6))
    x = np.arange(len(cwes))
    width = 0.2

    b1 = ax.bar(x - 1.5*width, recall, width, label='Recall (%)', color='#4361ee')
    b2 = ax.bar(x - 0.5*width, precision, width, label='Precision (%)', color='#2ec4b6')
    b3 = ax.bar(x + 0.5*width, f1, width, label='F1-Score (%)', color='#ff9f1c')
    b4 = ax.bar(x + 1.5*width, fpr, width, label='False Positive Rate (%) [Lower is Better]', color='#e71d36')

    # Add data labels
    for bars in [b1, b2, b3, b4]:
        for bar in bars:
            h = bar.get_height()
            if h > 2:
                ax.annotate(f'{h:.1f}%',
                            xy=(bar.get_x() + bar.get_width() / 2, h),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_title('Generalization Breakdown Across 5 Held-Out (Unseen) CWE Categories', fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(cwes, fontsize=10, fontweight='semibold')
    ax.set_ylabel('Percentage (%)', fontsize=11, fontweight='bold')
    ax.set_ylim(0, 115)
    ax.legend(loc='upper right', frameon=True, fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    save_path = os.path.join(FIGURES_DIR, "unseen_cwe_breakdown.png")
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[Chart] Saved: {save_path}")

# -------------------------------------------------------------
# 3. CHART: CONFUSION MATRICES
# -------------------------------------------------------------
def plot_confusion_matrices():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Seen: TP=846, FP=120, FN=3, TN=729
    cm_seen = np.array([[729, 120], [3, 846]])
    # Unseen: TP=847, FP=35, FN=211, TN=1023
    cm_unseen = np.array([[1023, 35], [211, 847]])

    for idx, (cm, title, ax) in enumerate([
        (cm_seen, 'Seen Categories Test Set (N = 1,698)', axes[0]),
        (cm_unseen, 'Unseen (Held-Out) Test Set (N = 2,116)', axes[1])
    ]):
        im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=12)
        
        tick_marks = np.arange(2)
        ax.set_xticks(tick_marks)
        ax.set_xticklabels(['Safe (0)', 'Vulnerable (1)'], fontsize=10)
        ax.set_yticks(tick_marks)
        ax.set_yticklabels(['Safe (0)', 'Vulnerable (1)'], fontsize=10)

        thresh = cm.max() / 2.
        for i in range(2):
            for j in range(2):
                val = cm[i, j]
                tag = ""
                if i == 0 and j == 0: tag = "TN"
                elif i == 0 and j == 1: tag = "FP"
                elif i == 1 and j == 0: tag = "FN"
                elif i == 1 and j == 1: tag = "TP"
                
                ax.text(j, i, f"{val}\n({tag})",
                        ha="center", va="center",
                        color="white" if val > thresh else "black",
                        fontsize=12, fontweight='bold')

        ax.set_ylabel('True Label', fontsize=11, fontweight='bold')
        ax.set_xlabel('Predicted Label', fontsize=11, fontweight='bold')
        ax.grid(False)

    plt.tight_layout()
    save_path = os.path.join(FIGURES_DIR, "confusion_matrices.png")
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[Chart] Saved: {save_path}")

# -------------------------------------------------------------
# 4. CHART: FRAMEWORK ARCHITECTURE DIAGRAM
# -------------------------------------------------------------
def plot_framework_architecture():
    fig, ax = plt.subplots(figsize=(15, 7))
    ax.axis('off')

    # Background canvas
    fig.patch.set_facecolor('#ffffff')

    def draw_box(x, y, w, h, text, color, text_color='#ffffff', title=''):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03", 
                                      facecolor=color, edgecolor='#222222', linewidth=1.5)
        ax.add_patch(rect)
        if title:
            ax.text(x + w/2, y + h - 0.05, title, ha='center', va='top', 
                    fontsize=10, fontweight='bold', color=text_color)
            ax.text(x + w/2, y + (h-0.05)/2, text, ha='center', va='center', 
                    fontsize=8.5, color=text_color)
        else:
            ax.text(x + w/2, y + h/2, text, ha='center', va='center', 
                    fontsize=9.5, fontweight='bold', color=text_color)

    def draw_arrow(x1, y1, x2, y2, label=''):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", lw=2, color='#333333'))
        if label:
            ax.text((x1+x2)/2, (y1+y2)/2 + 0.02, label, ha='center', va='bottom', fontsize=8, color='#555555')

    # 1. Input Code
    draw_box(0.03, 0.40, 0.16, 0.22, "Sanitized C/C++ Source Code\n• Leakage Tokens Removed\n• Comments & Directives Purged\n• Paired Vuln & Safe Functions", 
             '#3a0ca3', title='1. Input Source Code')

    # 2. Dual Pathways
    # Static branch
    draw_box(0.26, 0.65, 0.22, 0.25, 
             "• Unsafe API counters\n• Bounds check presence\n• Memory alloc/free delta\n• Unchecked returns (CWE-253)\n• Crypto primitives (CWE-327)\n• Direct format string (CWE-134)", 
             '#0077b6', title='Branch A: Static Analysis (48-D)')

    # LLM branch
    draw_box(0.26, 0.15, 0.22, 0.25, 
             "• Qwen2.5-Coder-0.5B-Instruct\n• Local RTX 3050 execution\n• Attention-masked mean pooling\n• Abstract code semantics\n• Unseen class transfer", 
             '#0096c7', title='Branch B: Code LLM (896-D)')

    draw_arrow(0.19, 0.55, 0.26, 0.77, "Static Extraction")
    draw_arrow(0.19, 0.47, 0.26, 0.27, "LLM Embeddings")

    # 3. Projections
    draw_box(0.53, 0.68, 0.14, 0.18, "Linear(48 -> 256)\n+ LayerNorm\n+ GELU + Dropout", '#48cae4', text_color='#000000', title='Static Proj (256-D)')
    draw_box(0.53, 0.18, 0.14, 0.18, "Linear(896 -> 256)\n+ LayerNorm\n+ GELU + Dropout", '#48cae4', text_color='#000000', title='LLM Proj (256-D)')

    draw_arrow(0.48, 0.77, 0.53, 0.77)
    draw_arrow(0.48, 0.27, 0.53, 0.27)

    # 4. Gated Cross-Modality Fusion
    draw_box(0.72, 0.35, 0.14, 0.34, 
             "Modality Gate:\ng = σ(W_g [h_llm; h_st] + b)\n\nFused Latent:\nh_fused = g * h_llm + (1-g) * h_st\n\nResidual Concatenation:\n[h_fused; h_llm; h_st]", 
             '#f77f00', title='Gated Fusion (GCFN)')

    draw_arrow(0.67, 0.77, 0.72, 0.58)
    draw_arrow(0.67, 0.27, 0.72, 0.46)

    # 5. Classifier & Decision
    draw_box(0.90, 0.40, 0.08, 0.24, "MLP Layer\n+\nThreshold Tuning\n(t = 0.45)", '#d62828', title='Decision')
    draw_arrow(0.86, 0.52, 0.90, 0.52)

    # Output annotation
    ax.text(0.94, 0.34, "Output:\n[Safe / Vuln]", ha='center', va='top', fontsize=9, fontweight='bold', color='#111111')

    # Title
    ax.text(0.5, 0.98, "LLM-Enhanced Static Analysis Framework Architecture", ha='center', va='top', 
            fontsize=16, fontweight='bold', color='#1d3557')

    plt.tight_layout()
    save_path = os.path.join(FIGURES_DIR, "framework_architecture.png")
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[Chart] Saved: {save_path}")

if __name__ == "__main__":
    print("[*] Generating publication-quality charts and diagrams...")
    plot_baseline_comparison()
    plot_unseen_breakdown()
    plot_confusion_matrices()
    plot_framework_architecture()
    print("[*] All figures successfully generated.")
