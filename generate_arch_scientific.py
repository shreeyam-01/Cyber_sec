import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

FIGURES_DIR = r"D:\cybersec_2\results\figures"
DESKTOP_DIR = r"C:\Users\Shreeyam Acharya\OneDrive\Desktop"
os.makedirs(FIGURES_DIR, exist_ok=True)

def draw_structured_architecture():
    # Set high-resolution figure with clean white background
    fig, ax = plt.subplots(figsize=(15.5, 9.2), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    fig.patch.set_facecolor('#ffffff')

    # Color Palette matching modern scientific publication standards (from Reference 1)
    BG_STAGE_1 = "#f8fafc"   # Clean off-white
    BG_STAGE_2 = "#f1f5f9"   # Light grey
    BORDER_STAGE = "#cbd5e1" # Slate border

    BOX_BLUE_LIGHT  = "#dbeafe" # Input/Static blue tint
    BOX_BLUE_BORDER = "#2563eb" # Blue stroke
    BOX_BLUE_TEXT   = "#1e3a8a"

    BOX_TEAL_LIGHT  = "#ccfbf1" # LLM teal/cyan tint
    BOX_TEAL_BORDER = "#0d9488"
    BOX_TEAL_TEXT   = "#115e59"

    BOX_ORANGE_LIGHT  = "#ffedd5" # Proj / Fusion warm tint
    BOX_ORANGE_BORDER = "#ea580c"
    BOX_ORANGE_TEXT   = "#9a3412"

    BOX_PURPLE_LIGHT  = "#f3e8ff" # Gating / Dynamic fusion
    BOX_PURPLE_BORDER = "#9333ea"
    BOX_PURPLE_TEXT   = "#6b21a8"

    BOX_RED_LIGHT  = "#ffe4e6" # Decision / Output red/rose tint
    BOX_RED_BORDER = "#e11d48"
    BOX_RED_TEXT   = "#881337"

    # Helper: draw outer horizontal stage swimlane
    def draw_stage(y_bottom, height, stage_title, bg_color=BG_STAGE_1):
        rect = patches.FancyBboxPatch(
            (1, y_bottom), 98, height,
            boxstyle="round,pad=0.2",
            facecolor=bg_color,
            edgecolor=BORDER_STAGE,
            linewidth=1.2
        )
        ax.add_patch(rect)
        # Stage title on top-left inside lane
        ax.text(2.2, y_bottom + height - 2.8, stage_title,
                fontsize=11.5, fontweight='bold', color="#0f172a", va="top", ha="left")

    # Helper: draw component block
    def draw_block(x, y, w, h, title, subtitle_lines, facecolor, edgecolor, title_color="#0f172a"):
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.4",
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=1.4
        )
        ax.add_patch(rect)
        if title:
            ax.text(x + w / 2, y + h - 2.0, title,
                    fontsize=10.2, fontweight='bold', color=title_color, ha='center', va='top')
        if subtitle_lines:
            text_str = "\n".join(subtitle_lines)
            ax.text(x + w / 2, y + (h - 2.2) / 2, text_str,
                    fontsize=8.5, color="#1e293b", ha='center', va='center', linespacing=1.3)

    # Helper: draw standard arrow
    def draw_arrow(x1, y1, x2, y2, color="#334155", lw=1.5, text=""):
        ax.annotate(
            '', xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="-|>", lw=lw, color=color, mutation_scale=11)
        )
        if text:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.9, text,
                    fontsize=8.2, fontweight='bold', color="#475569", ha='center', va='bottom')

    # =========================================================================
    # STAGE 1: Inputs & Sanitization Engine (y: 84 to 98)
    # =========================================================================
    draw_stage(84, 14, "Stage 1: Input Code & Leakage-Proof Sanitization", BG_STAGE_1)
    
    draw_block(12, 85.5, 34, 9.5,
               "Raw C/C++ Source Functions",
               ["NIST Juliet C/C++ Test Suite v1.3",
                "Pairs of Vulnerable & Fixed Safe Counterparts"],
               "#ffffff", "#94a3b8")
    
    draw_arrow(46, 90.2, 53.5, 90.2, text="Sanitize")

    draw_block(54, 85.5, 41, 9.5,
               "Automated Sanitization Engine",
               ["• Purges flaw/fix comments & #ifndef OMITBAD/OMITGOOD",
                "• Strips function name markers (_bad, _good) & leakage variables"],
               BOX_BLUE_LIGHT, BOX_BLUE_BORDER, BOX_BLUE_TEXT)

    # =========================================================================
    # STAGE 2: Dual-Modality Feature Encoders (y: 61 to 81)
    # =========================================================================
    draw_stage(61, 20.5, "Stage 2: Dual-Branch Feature Encoders (Static Analysis + Code LLM)", BG_STAGE_2)

    # Branch A: Static Analysis
    draw_block(6, 63.5, 41, 14.5,
               "Branch A: Static Analysis Feature Extractor (48-D)",
               ["• Memory Allocation / Free Lifecycle Deltas (malloc, free)",
                "• Unsafe vs Bounds-Checked String APIs (strcpy vs strncpy)",
                "• Pointer Dereferences & Array Subscript Indices",
                "• Return-Value Check Omissions (fputs, remove; CWE-253)",
                "• Boundary Limits & Casts (INT_MAX; CWE-190/191)",
                "• Format String Risks (CWE-134) & Weak Crypto (CWE-327)"],
               BOX_BLUE_LIGHT, BOX_BLUE_BORDER, BOX_BLUE_TEXT)

    # Branch B: Code LLM
    draw_block(53, 63.5, 41, 14.5,
               "Branch B: Local Pretrained Code LLM (896-D)",
               ["• Qwen2.5-Coder-0.5B-Instruct Backbone",
                "• Executed Locally on RTX 3050 Laptop GPU (~950 MB VRAM)",
                "• Token Sequence Encoding (Contextual Program Intent)",
                "• Attention-Masked Mean Pooling across Token Dimension",
                "• Zero Cloud Dependencies & Total Source Privacy"],
               BOX_TEAL_LIGHT, BOX_TEAL_BORDER, BOX_TEAL_TEXT)

    # Arrows from Stage 1 to Stage 2
    # Branching from Sanitization block (center x=74.5, bottom y=85.5)
    draw_arrow(74.5, 85.5, 26.5, 78.0, color="#2563eb", text="Token Stream")
    draw_arrow(74.5, 85.5, 73.5, 78.0, color="#0d9488", text="Code Text")

    # =========================================================================
    # STAGE 3: Latent Projections & Modality Alignment (y: 43 to 58)
    # =========================================================================
    draw_stage(43, 15.5, "Stage 3: Latent Projections & Feature Normalization", BG_STAGE_1)

    draw_block(10, 45.0, 34, 10.5,
               "Static Projection MLP (256-D)",
               ["BatchNorm1d(48)",
                "→ Linear(48 → 256) → LayerNorm → GELU",
                "→ Dropout(0.3) → Linear(256 → 256) → LayerNorm"],
               BOX_ORANGE_LIGHT, BOX_ORANGE_BORDER, BOX_ORANGE_TEXT)

    draw_block(56, 45.0, 34, 10.5,
               "LLM Semantic Projection MLP (256-D)",
               ["LayerNorm(896)",
                "→ Linear(896 → 256) → LayerNorm → GELU",
                "→ Dropout(0.3) → Linear(256 → 256) → LayerNorm"],
               BOX_ORANGE_LIGHT, BOX_ORANGE_BORDER, BOX_ORANGE_TEXT)

    draw_arrow(26.5, 63.5, 26.5, 55.5, text="x_st (48-D)")
    draw_arrow(73.5, 63.5, 73.5, 55.5, text="h_llm (896-D)")

    # =========================================================================
    # STAGE 4: Gated Cross-Modality Fusion (GCFN) (y: 24 to 40)
    # =========================================================================
    draw_stage(24, 16.5, "Stage 4: Gated Cross-Modality Fusion Network (GCFN)", BG_STAGE_2)

    # Left: Modality Gate
    draw_block(8, 26.0, 38, 11.5,
               "Dynamic Modality Gating Unit",
               ["g = σ( W_g [z_static; z_llm] + b_g )",
                "g ∈ [0, 1]²⁵⁶ : Adaptive Feature-Wise Balance",
                "Concrete Bounds Hazards ↔ High-Level Intent"],
               BOX_PURPLE_LIGHT, BOX_PURPLE_BORDER, BOX_PURPLE_TEXT)

    # Right: Fused Representation & Residual Concatenation
    draw_block(52, 26.0, 42, 11.5,
               "Fused Latent & Residual Concatenation",
               ["z_fused = g ⊙ z_llm + (1 - g) ⊙ z_static",
                "Joint Residual Representation:",
                "Z_joint = [ z_fused ; z_llm ; z_static ]  (768-D)",
                "Preserves Independent Modality Invariants"],
               BOX_PURPLE_LIGHT, BOX_PURPLE_BORDER, BOX_PURPLE_TEXT)

    # Arrows from Stage 3 into Gating and Fusion
    draw_arrow(26.5, 45.0, 26.5, 37.5, text="z_st (256-D)")
    draw_arrow(73.5, 45.0, 73.5, 37.5, text="z_llm (256-D)")
    draw_arrow(46.0, 31.7, 52.0, 31.7, text="Gate Vector g")

    # =========================================================================
    # STAGE 5: Classification Head & Threshold Decision (y: 1 to 21)
    # =========================================================================
    draw_stage(1, 20.5, "Stage 5: Joint Classification Head & Calibrated Inference", BG_STAGE_1)

    draw_block(10, 4.0, 38, 14.5,
               "Classification MLP Head",
               ["LayerNorm(768) → Dropout(0.3)",
                "→ Linear(768 → 256) → GELU → Dropout(0.15)",
                "→ Linear(256 → 1) → Logit Output",
                "Optimization: AdamW + Cosine Annealing",
                "Trained Exclusively on 15 Seen CWE Categories"],
               BOX_RED_LIGHT, BOX_RED_BORDER, BOX_RED_TEXT)

    draw_arrow(73.0, 26.0, 30.0, 18.5, color="#e11d48", text="Z_joint (768-D)")

    draw_block(54, 4.0, 41, 14.5,
               "Decision Head & Zero-Shot Evaluation",
               ["Sigmoid Activation: P(Vulnerable) = σ(logit)",
                "Validation Calibrated Threshold: θ = 0.45",
                "--------------------------------------------------",
                "• Seen CWE Evaluation: 99.65% Recall, 93.22% F1",
                "• Unseen Held-Out Generalization: 80.06% Recall,",
                "  96.03% Precision, 3.31% False Positive Rate"],
               BOX_RED_LIGHT, BOX_RED_BORDER, BOX_RED_TEXT)

    draw_arrow(48.0, 11.2, 54.0, 11.2, color="#e11d48", text="Logit Score")

    # Save to D:\cybersec_2 and Desktop
    save_fig = os.path.join(FIGURES_DIR, "framework_architecture_scientific.png")
    save_desktop = os.path.join(DESKTOP_DIR, "framework_architecture_scientific.png")
    
    plt.savefig(save_fig, dpi=300, bbox_inches='tight')
    plt.savefig(save_desktop, dpi=300, bbox_inches='tight')
    plt.close()
    print("Scientific architecture diagram generated successfully:")
    print("  1.", save_desktop)
    print("  2.", save_fig)

if __name__ == "__main__":
    draw_structured_architecture()
