import os
import matplotlib.pyplot as plt

FIGURES_DIR = r"D:\cybersec_2\results\figures"
os.makedirs(FIGURES_DIR, exist_ok=True)

def generate_gantt_chart():
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    
    tasks = [
        "Task 1: Literature Review & Dataset Inspection",
        "Task 2: Sanitization & Leakage Prevention",
        "Task 3: Static Feature Extractor (48-D)",
        "Task 4: Local Code-LLM Semantic Pipeline",
        "Task 5: Gated Cross-Modality Fusion (GCFN)",
        "Task 6: Validation Tuning & Baseline Comparison",
        "Task 7: Report & Dashboard Preparation"
    ]
    
    # Months: July, August, September, October
    # 16 weeks total across the 4 months:
    # July (W1-W4), August (W5-W8), September (W9-W12), October (W13-W16)
    start_weeks = [1, 2.5, 4.5, 7, 9.5, 12, 14]
    durations   = [2.5, 2.5, 3.5, 3.5, 3.5, 2.5, 2]
    
    colors = ['#2b5c8f', '#2a9d8f', '#e76f51', '#7209b7', '#3a86ff', '#38b000', '#f77f00']
    
    for i, (task, start, dur, col) in enumerate(zip(tasks, start_weeks, durations, colors)):
        ax.barh(task, dur, left=start, height=0.48, align='center', color=col, edgecolor='#222222', alpha=0.88)
        
    ax.set_xlabel('Project Timeline (Months: July – October)', fontsize=11, fontweight='bold', labelpad=10)
    ax.set_xlim(0.5, 16.5)
    ax.set_xticks([1, 5, 9, 13, 16])
    ax.set_xticklabels(['July', 'August', 'September', 'October', 'End Oct'], fontsize=10, fontweight='bold')
    
    ax.invert_yaxis()  # Top-down order
    ax.grid(axis='x', linestyle='--', alpha=0.6)
    ax.set_title('Figure 1: Project Implementation Gantt Chart', fontsize=13, fontweight='bold', pad=14)
    
    plt.tight_layout()
    save_path = os.path.join(FIGURES_DIR, "gantt_chart.png")
    plt.savefig(save_path, dpi=300)
    plt.close()
    print("Gantt chart successfully updated with July-October timeline:", save_path)

if __name__ == "__main__":
    generate_gantt_chart()
