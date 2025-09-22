# /src/rag/indexer.py
# Build/save/load HNSW index; controls M/efConstruction/efSaerch

from __future__ import annotations
import os
import json
from typing import List, Dict, Any
import numpy as np
import hnswlib   # pip install hnswlib

from rag.interfaces import VectorIndex

# Hierarchical Navigable Small World (HNSW) Index
class HnswIndex(VectorIndex):
    def __init__(self, ef_construction: int = 200, M: int = 16, ef: int = 128):

        # Placeholder for the HNSW objects
        self.index = None

        # vector dimensions
        self.dim = None

        # distance metric
        self.space = "cosine"

        # exploration factor: higher -> better recall quality/ slower and more memory intensive
        self.ef_construction = ef_construction

        # count for bi-directional links; higher -> better recall quality/ more memory
        self.M = M

        # exploration factor at query time: higher -> more neighbors are searched, better recall, slower and more memory intensive
        self.ef = ef
        self.meta: List[Dict[str, Any]] = []  # aligned with ID -> metadata+text

    def build(self, dim: int, space: str = "cosine") -> None:
        self.dim = dim
        self.space = space
        self.index = hnswlib.Index(space=space, dim=dim)
        # heuristic: capacity grows as we add; start with 10k
        self.index.init_index(max_elements=10_000, ef_construction=self.ef_construction, M=self.M)
        self.index.set_ef(self.ef)

    def upsert(self, vectors: List[List[float]], metas: List[Dict[str, Any]]) -> None:
        assert self.index is not None, "Index not built"
        arr = np.asarray(vectors, dtype=np.float32)
        start_id = len(self.meta)
        ids = np.arange(start_id, start_id + arr.shape[0])
        self.index.add_items(arr, ids)
        self.meta.extend(metas)

    def query(self, vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        assert self.index is not None, "Index not built/loaded"
        q = np.asarray([vector], dtype=np.float32)
        labels, dists = self.index.knn_query(q, k=k)
        out: List[Dict[str, Any]] = []
        for idx, dist in zip(labels[0], dists[0]):
            m = self.meta[int(idx)]
            out.append({"text": m["text"], "meta": {k:v for k,v in m.items() if k != "text"}, "score": float(dist)})
        return out

    def save(self, path: str) -> None:
        assert self.index is not None, "Index not built"
        os.makedirs(path, exist_ok=True)
        self.index.save_index(os.path.join(path, "hnsw.bin"))
        with open(os.path.join(path, "meta.jsonl"), "w", encoding="utf-8") as f:
            for m in self.meta:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")

    def load(self, path: str) -> None:
        # you must know dim/space; store it in meta header or infer by re-embedding one
        # for simplicity, store it inside meta.jsonl first line
        meta_path = os.path.join(path, "meta.jsonl")
        assert os.path.exists(meta_path), "meta.jsonl missing"
        self.meta = []
        with open(meta_path, "r", encoding="utf-8") as f:
            for line in f:
                self.meta.append(json.loads(line))
        assert len(self.meta) > 0, "no metadata found"
        header = self.meta[0].get("_index_header")
        assert header, "missing _index_header in first meta"
        self.dim = header["dim"]; self.space = header["space"]
        self.index = hnswlib.Index(space=self.space, dim=self.dim)
        self.index.load_index(os.path.join(path, "hnsw.bin"))
        self.index.set_ef(self.ef)

