import torch
import torch.nn as nn
import torch.nn.functional as F

class LLMEnhancedStaticClassifier(nn.Module):
    """
    Gated Cross-Modality Fusion Network combining
    Static Analysis domain features with LLM semantic embeddings.
    """
    def __init__(
        self,
        static_dim: int = 48,
        llm_dim: int = 896,
        hidden_dim: int = 256,
        dropout: float = 0.3
    ):
        super().__init__()
        
        # Static Analysis projection branch
        self.static_norm = nn.BatchNorm1d(static_dim)
        self.static_proj = nn.Sequential(
            nn.Linear(static_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU()
        )
        
        # LLM Semantic projection branch
        self.llm_proj = nn.Sequential(
            nn.Linear(llm_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU()
        )
        
        # Modality Gating Unit
        self.gate_layer = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.Sigmoid()
        )
        
        # Joint Classification MLP
        combined_dim = hidden_dim * 3
        self.classifier = nn.Sequential(
            nn.LayerNorm(combined_dim),
            nn.Dropout(dropout),
            nn.Linear(combined_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout / 2),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, static_feats: torch.Tensor, llm_feats: torch.Tensor) -> torch.Tensor:
        # Normalize and project static features
        normed_static = self.static_norm(static_feats)
        h_static = self.static_proj(normed_static)
        
        # Project LLM semantic features
        h_llm = self.llm_proj(llm_feats)
        
        # Compute dynamic gating weights
        concat_h = torch.cat([h_static, h_llm], dim=-1)
        gate = self.gate_layer(concat_h)
        
        # Gated fusion with residual pathways
        h_fused = gate * h_llm + (1.0 - gate) * h_static
        joint = torch.cat([h_fused, h_llm, h_static], dim=-1)
        
        # Final logit
        logits = self.classifier(joint).squeeze(-1)
        return logits
