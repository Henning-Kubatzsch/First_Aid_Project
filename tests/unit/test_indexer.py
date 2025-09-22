# tests/unit/test_indexer.py
import json
import os
import numpy as np
import pytest

from rag.indexer import HnswIndex


def _with_header(idx: HnswIndex, dim: int, space: str = "cosine"):
    """
    NOTE:
    HnswIndex.load() expects the first line in meta.jsonl to be a header:
      {"_index_header": {"dim": <int>, "space": "<space>"}, "text": ""}
    We insert this BEFORE the first upsert() so that:
      - index IDs start at 1,
      - meta[0] is the header (never queried),
      - save/load works without extra code.
    """
    idx.meta = [{"_index_header": {"dim": dim, "space": space}, "text": ""}]


def test_errors_if_not_built():
    idx = HnswIndex()
    with pytest.raises(AssertionError):
        idx.upsert([[1.0, 0.0, 0.0]], [{"text": "a"}])
    with pytest.raises(AssertionError):
        idx.query([1.0, 0.0, 0.0], k=1)


def test_build_upsert_query_cosine_basic():
    idx = HnswIndex(ef_construction=50, M=8, ef=64)
    dim = 3
    idx.build(dim=dim, space="cosine")
    _with_header(idx, dim=dim, space="cosine")

    # Orthogonal unit vectors: identical -> distance ~0.0, orthogonal -> ~1.0
    vecs = [
        [1.0, 0.0, 0.0],  # A
        [0.0, 1.0, 0.0],  # B
        [0.0, 0.0, 1.0],  # C
    ]
    metas = [
        {"text": "A", "id": 1},
        {"text": "B", "id": 2},
        {"text": "C", "id": 3},
    ]

    idx.upsert(vecs, metas)

    res = idx.query([1.0, 0.0, 0.0], k=3)
    # Top-1 must be "A", score ~ 0.0 (cosine distance for identical vector)
    assert res[0]["text"] == "A"
    assert isinstance(res[0]["score"], float)
    assert res[0]["score"] == pytest.approx(0.0, abs=1e-6)

    # Meta must NOT contain "text", but keep custom fields
    assert "text" not in res[0]["meta"]
    assert res[0]["meta"]["id"] == 1

    # Exactly 3 results (since k=3 and 3 items present)
    assert len(res) == 3


def test_save_and_load_roundtrip(tmp_path):
    idx = HnswIndex(ef_construction=50, M=8, ef=64)
    dim = 2
    idx.build(dim=dim, space="cosine")
    _with_header(idx, dim=dim, space="cosine")

    vecs = [
        [1.0, 0.0],  # X
        [0.0, 1.0],  # Y
    ]
    metas = [
        {"text": "X", "doc_id": "x1"},
        {"text": "Y", "doc_id": "y1"},
    ]
    idx.upsert(vecs, metas)

    save_dir = tmp_path / "hnsw"
    idx.save(str(save_dir))

    # Files exist
    assert (save_dir / "hnsw.bin").exists()
    assert (save_dir / "meta.jsonl").exists()

    # First line in meta.jsonl is the header
    with open(save_dir / "meta.jsonl", "r", encoding="utf-8") as f:
        first = json.loads(f.readline())
    assert "_index_header" in first
    assert first.get("text", "") == ""

    # New instance and load
    idx2 = HnswIndex()
    idx2.load(str(save_dir))

    # Query returns same top results
    res = idx2.query([1.0, 0.0], k=2)
    assert res[0]["text"] == "X"
    assert res[0]["score"] == pytest.approx(0.0, abs=1e-6)
    assert res[0]["meta"]["doc_id"] == "x1"
