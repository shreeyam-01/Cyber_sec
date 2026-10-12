import os
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
from typing import List

class LLMFeatureEncoder:
    """
    Lightweight LLM Code Semantic Encoder based on Qwen2.5-Coder-0.5B-Instruct.
    Extracts deep semantic representations of code logic.
    """
    def __init__(self, model_id: str = "Qwen/Qwen2.5-Coder-0.5B-Instruct", device: str = "cuda", max_len: int = 256):
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.max_len = max_len
        print(f"[LLM Encoder] Initializing tokenizer & model from {model_id} on {self.device}...")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        dtype = torch.float16 if self.device.type == "cuda" else torch.float32
        self.model = AutoModel.from_pretrained(
            model_id,
            local_files_only=True,
            dtype=dtype
        ).to(self.device)
        self.model.eval()
        self.embedding_dim = self.model.config.hidden_size # 896 for Qwen2.5-Coder-0.5B
        print(f"[LLM Encoder] Ready. Embedding dimension: {self.embedding_dim}")

    @torch.no_grad()
    def encode_batch(self, texts: List[str], batch_size: int = 32) -> torch.Tensor:
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            encoded = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=self.max_len,
                return_tensors="pt"
            ).to(self.device)
            
            outputs = self.model(**encoded)
            # Use attention-masked mean pooling for robust representation
            mask = encoded["attention_mask"].unsqueeze(-1)
            sum_embeddings = (outputs.last_hidden_state * mask).sum(dim=1)
            sum_mask = mask.sum(dim=1).clamp(min=1e-9)
            mean_pooled = (sum_embeddings / sum_mask).cpu().float()
            
            all_embeddings.append(mean_pooled)
            
        return torch.cat(all_embeddings, dim=0)

    def extract_or_load_embeddings(self, texts: List[str], cache_path: str, batch_size: int = 32) -> torch.Tensor:
        if os.path.exists(cache_path):
            print(f"[LLM Encoder] Loading cached embeddings from {cache_path}")
            return torch.load(cache_path, weights_only=True)
            
        print(f"[LLM Encoder] Extracting embeddings for {len(texts)} samples...")
        embeddings = self.encode_batch(texts, batch_size=batch_size)
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        torch.save(embeddings, cache_path)
        print(f"[LLM Encoder] Saved embeddings to {cache_path}")
        return embeddings
