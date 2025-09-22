from __future__ import annotations
import os, json
from typing import List, Dict, Any

from rag.chunk import ParagraphChunker
from rag.custom_chunk import CustomChunker
from rag.embed import SBertEmbeddings
from rag.indexer import HnswIndex

def read_docs(docs_dir: str) -> List[Dict[str, Any]]:
    items = []
    for name in os.listdir(docs_dir):
        p = os.path.join(docs_dir, name)
        if not os.path.isfile(p): continue
        if not name.lower().endswith((".txt", ".md")): continue
        with open(p, "r", encoding="utf-8") as f:
            txt = f.read()
        items.append({"source": name, "text": txt})
    return items

def build_erc_index(
    docs_dir: str = "data/docs",
    out_dir: str = "data/index",
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    target_chars: int = 400,
    custom_chunker: bool = False, 
) -> None:
    print(f"custom chunker: {custom_chunker}")

    os.makedirs(out_dir, exist_ok=True)
    docs = read_docs(docs_dir)
    chunker = None

    if(custom_chunker):
        chunker = CustomChunker()        
    else:
        chunker = ParagraphChunker(target_chars=target_chars)
        

    embedder = SBertEmbeddings(model_name=model_name)
    dim_probe = len(embedder.embed_one("probe"))

    print(f"dim_probe: {dim_probe}")
    
    index = HnswIndex()
    index.build(dim=dim_probe, space="cosine")

    vectors: List[List[float]] = []
    metas: List[Dict[str, Any]] = []

    # Store index header in the first meta row for reload
    header_written = False  

    print("="*20)
    print(len(docs), "documents to index")
    print("="*20)

    index_value = None
    if custom_chunker:
        index_value = "question"
    else:
        index_value = "text"


    for d in docs:
        chunks = chunker.split(d["text"], meta={"source": d["source"]})
        texts = [c[index_value] for c in chunks]
        embs = embedder.embed(texts)
        for c, v in zip(chunks, embs):
            m = {"id": c["id"], "source": d["source"], "text": c["text"]}
            if not header_written:
                m["_index_header"] = {"dim": dim_probe, "space": "cosine"}
                header_written = True
            vectors.append(v)
            metas.append(m)

    

    index.upsert(vectors, metas)
    index.save(out_dir)

if __name__ == "__main__":
    build_erc_index()
