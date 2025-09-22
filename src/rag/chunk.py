# src/rag/chunk.py
from __future__ import annotations
import re
import hashlib
from typing import List, Dict, Any, Optional
from rag.interfaces import Chunker


class ParagraphChunker(Chunker):
    """
    Simple, deterministic paragraph splitter with approximate size control.
    - Splits on blank lines (paragraphs)
    - Merges paragraphs until target_chars (but ensures >= min_chars)
    - Adds character overlap *between* emitted chunks (never before the first)
    """

    ## def __init__(self, target_chars: int = 1200, min_chars: int = 400, overlap_chars: int = 120):
    def __init__(self, target_chars: int = 400, min_chars: int = 200, overlap_chars: int = 120):
        self.target = target_chars
        self.min = min_chars
        self.overlap = overlap_chars

    def _norm(self, txt: str) -> str:
        txt = txt.replace("\r", "")
        txt = re.sub(r'\n{2,}', '\n\n', txt)
        return txt.strip()


    def split(self, text: str, meta: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:

        print("we are in standard chunker")

        meta = meta or {}
        text = self._norm(text)

        # paragraphs are separated by blank lines
        paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

        chunks: List[Dict[str, Any]] = []
        buf: List[str] = []
        size = 0
        last_chunk_text: Optional[str] = None  # text of last emitted chunk (for safe overlap)

        def emit() -> Optional[Dict[str, Any]]:
            """Emit current buffer as a chunk and reset buffer/size."""
            nonlocal buf, size, last_chunk_text
            if not buf:
                return None
            chunk_text = "\n\n".join(buf).strip()
            cid = hashlib.sha1(chunk_text.encode("utf-8")).hexdigest()[:16]
            out = {"id": cid, "text": chunk_text, "meta": dict(meta)}
            chunks.append(out)
            last_chunk_text = chunk_text
            buf, size = [], 0
            return out

        i = 0
        while i < len(paras):
            p = paras[i]
            # keep adding paragraphs while under target OR we haven't reached min yet
            if size + len(p) <= self.target or size < self.min:
                buf.append(p)
                size += len(p)
                i += 1
            else:
                # emit current buffer as a chunk
                emitted = emit()
                # prepare next buffer with overlap — only AFTER first chunk exists
                if self.overlap and emitted is not None and last_chunk_text:
                    tail = last_chunk_text[-self.overlap:]
                    # Optional: shift to word boundary (uncomment next 3 lines if desired)
                    # ws = tail.find(" ")
                    # if ws != -1 and ws + 1 < len(tail):
                    #     tail = tail[ws + 1 :]
                    buf = [tail]
                    size = len(tail)

        # emit remainder
        emit()
        return chunks
