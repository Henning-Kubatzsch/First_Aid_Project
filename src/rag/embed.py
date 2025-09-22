# Load embedding model; encode chunks/questions -> vectors (np.ndarray)

from __future__ import annotations
from typing import List
from rag.interfaces import Embedder

# sentence-transformers uses torch under the hood (already env)
from sentence_transformers import SentenceTransformer

class SBertEmbeddings(Embedder):
    """
    Small, fast local embedding model. Good starters:
    - 'sentence-transformers/all-MiniLM-L6-v2' (384d)
    - 'nomic-ai/nomic-embed-text-v1.5' (768d, may require extra install)
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu"):
        self.model = SentenceTransformer(model_name, device=device)

    def embed(self, texts: List[str]) -> List[List[float]]:
        embs = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False, normalize_embeddings=True)
        return [e.tolist() for e in embs]

    def embed_one(self, text: str) -> List[float]:
        return self.embed([text])[0]
