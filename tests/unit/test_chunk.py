# tests/unit/test_chunker.py
import re
from rag.chunk import ParagraphChunker

def is_hex16(s: str) -> bool:
    return len(s) == 16 and re.fullmatch(r"[0-9a-f]{16}", s) is not None


def test_normalization_collapses_blank_lines_and_crlf():
    ch = ParagraphChunker(target_chars=200, min_chars=1, overlap_chars=10)
    raw = "A\r\n\r\n\r\n  \nB\n\n\nC"
    out = ch.split(raw)
    # Erwartung: CR weg, viele Blanklines -> genau eine Leerzeile
    assert len(out) == 1
    assert out[0]["text"] == "A\n\nB\n\nC"


def test_split_on_blank_lines_and_merge_until_target_no_overlap():
    # kleine Paragraphen, kleines target => mehrere Chunks
    ch = ParagraphChunker(target_chars=6, min_chars=1, overlap_chars=0)
    text = "AAAA\n\nBBBBB\n\nCC"  # Längen: 4, 5, 2
    out = ch.split(text)
    assert [c["text"] for c in out] == ["AAAA", "BBBBB", "CC"]


def test_overlap_inserted_between_chunks_but_not_before_first():
    # so wählen, dass nach erstem Chunk gesplittet wird,
    # aber Overlap + nächster Paragraph <= target bleibt
    ch = ParagraphChunker(target_chars=7, min_chars=1, overlap_chars=2)
    text = "Hello\n\nWorld"
    out = ch.split(text)
    assert len(out) == 2
    assert out[0]["text"] == "Hello"
    # Zweiter Chunk beginnt mit den letzten 2 Zeichen des ersten Chunks
    assert out[1]["text"].startswith("lo")
    # Overlap wird nicht vor dem ersten Chunk eingefügt
    assert not out[0]["text"].startswith("lo")


def test_meta_is_copied_not_shared():
    ch = ParagraphChunker(target_chars=100, min_chars=1, overlap_chars=0)
    meta = {"a": 1}
    out = ch.split("X", meta=meta)
    meta["a"] = 2  # nachträgliche Änderung darf Chunk nicht beeinflussen
    assert out[0]["meta"] == {"a": 1}


def test_chunk_id_is_deterministic_and_hex16():
    ch = ParagraphChunker(target_chars=100, min_chars=1, overlap_chars=0)
    o1 = ch.split("Same text")
    o2 = ch.split("Same text")
    o3 = ch.split("Different text")
    assert o1[0]["id"] == o2[0]["id"]
    assert o1[0]["id"] != o3[0]["id"]
    assert is_hex16(o1[0]["id"]) and is_hex16(o3[0]["id"])


def test_min_chars_forces_merge_even_if_over_target():
    # min_chars sorgt dafür, dass weiter gemerged wird, auch wenn target überschritten würde
    ch = ParagraphChunker(target_chars=3, min_chars=5, overlap_chars=0)
    text = "aa\n\nbb\n\ncc"  # Längen: 2, 2, 2 => Summe 6
    out = ch.split(text)
    assert len(out) == 1
    assert out[0]["text"] == "aa\n\nbb\n\ncc"


def test_empty_or_whitespace_input_yields_no_chunks():
    ch = ParagraphChunker(target_chars=100, min_chars=1, overlap_chars=0)
    assert ch.split("") == []
    assert ch.split("   \n \n\t  ") == []
