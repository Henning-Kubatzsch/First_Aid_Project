# src/rag/prompt.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, List, Dict, Tuple
import re
import textwrap

# ----------------------------
# Public API (du nutzt diese)
# ----------------------------

@dataclass
class PromptOptions:
    language: str = "en"             # "en" | "de"
    style: str = "steps"             # "steps" | "qa"
    max_context_chars: int = 4000    # Budget für Kontext
    cite: bool = True                # [1], [2] Zitate
    require_citations: bool = True   # Antwort MUSS [n] enthalten, sonst Hinweis anhängen

def build_prompts(
    question: str,
    hits: List[Dict],
    opts: PromptOptions | None = None
) -> Tuple[str, str]:
    """
    Liefert (system, user) Strings. `hits` sind die Retriever-Dokumente:
    [{'text': str, 'meta': {...}, 'score': float}, ...]
    """
    opts = opts or PromptOptions()

    # 1) Kontext + Bibliographie
    context, bib = _build_context_and_bib(hits, max_chars=opts.max_context_chars)

    # 2) System-Message
    system = _system_prompt(opts, bib)

    # 3) User-Message
    if opts.cite:
        user = f"Context:\n{context}\n\nQuestion:\n{question}\n\n" \
               f"Answer rules:\n{_answer_rules(opts)}"
    else:
        user = f"Context:\n{context}\n\nQuestion:\n{question}\n\n" \
               f"Answer rules:\n{_answer_rules(opts, cite=False)}"

    return system, user

def postprocess_answer(
    answer: str,
    num_sources: int,
    opts: PromptOptions | None = None
) -> str:
    """
    Räumt typische Artefakte auf und stellt sicher, dass Format & Zitate passen.
    """
    opts = opts or PromptOptions()
    a = _normalize(answer)

    # Entferne LLM-Markup/Stops
    a = re.sub(r"</s>|<\|endoftext\|>|\[/?assistant\]|\[/?user\]", "", a, flags=re.I)

    # Liste erzwingen (wenn Steps-Style)
    if opts.style == "steps" and not re.search(r"^\s*1[.)]", a, flags=re.M):
        a = _force_numbered_list(a)

    # Zitate säubern: nur [1..num_sources] erlauben
    if opts.cite:
        a = _clamp_citations(a, max_n=max(1, num_sources))

    # Falls gefordert, aber keine Zitate vorhanden → Hinweis anhängen
    if opts.cite and opts.require_citations and not re.search(r"\[\d+]", a):
        a += "\n\nNote: No specific source index was cited. Verify with context."

    # Geräusche entfernen & Straffung
    a = a.strip()
    return a if a else "I'm unsure. Please consult a medical professional."

# ----------------------------
# Internals (Hilfsfunktionen)
# ----------------------------

def _build_context_and_bib(hits: List[Dict], max_chars: int) -> Tuple[str, str]:
    """
    Schneidet Kontext auf ein Zeichenbudget und baut eine kurze Bibliographie.
    """
    cleaned = []
    total = 0
    for i, h in enumerate(hits, start=1):
        txt = _squash(h.get("text", ""), hard_trim=1200)
        entry = f"[{i}] {txt}"
        if total + len(entry) > max_chars:
            break
        cleaned.append(entry)
        total += len(entry)

    context = "\n\n".join(cleaned)

    bib_lines = []
    for i, h in enumerate(hits, start=1):
        m = h.get("meta", {}) or {}
        title = m.get("title") or m.get("doc") or "Unknown"
        sec = m.get("section") or m.get("page") or ""
        year = m.get("year") or ""
        extra = f", {sec}" if sec else ""
        year_str = f" ({year})" if year else ""
        bib_lines.append(f"[{i}] {title}{extra}{year_str}")

    bib = "\n".join(bib_lines)
    return context, bib

def _system_prompt(opts: PromptOptions, bib: str) -> str:
    if opts.language == "de":
        rules = textwrap.dedent(f"""
        Du bist ein knapper, sicherheitsbewusster Assistent, ausgerichtet an ERC/First-Aid-Guidelines.
        Antworte kurz, korrekt, mit klaren Schritten. Wenn du unsicher bist, sage es explizit.
        Wenn Kontextzitate vorhanden sind, zitiere mit [1], [2], … entsprechend der Quelle.
        Quellen:
        {bib}
        """).strip()
    else:
        rules = textwrap.dedent(f"""
        You are a concise, safety-first assistant aligned with ERC/first-aid guidelines.
        Answer briefly and correctly with clear steps. If unsure, say so explicitly.
        When context citations exist, cite [1], [2], … matching the source list.
        Sources:
        {bib}
        """).strip()
    return rules

def _answer_rules(opts: PromptOptions, cite: bool = True) -> str:
    if opts.language == "de":
        base = [
            "Use short, numbered steps (1., 2., 3.).",
            "Be precise and safe-first.",
            "If unsure, say: 'Ich bin unsicher.'",
        ]
        if cite and opts.cite:
            base.append("Cite sources using [n] that refer to the numbered context chunks.")
    else:
        base = [
            "Use short, numbered steps (1., 2., 3.).",
            "Be precise and safety-first.",
            "If unsure, say: 'I'm unsure.'",
        ]
        if cite and opts.cite:
            base.append("Cite sources using [n] that refer to the numbered context chunks.")
    return "- " + "\n- ".join(base)

def _normalize(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    # collapse excessive blank lines
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def _squash(s: str, hard_trim: int = 1200) -> str:
    s = _normalize(s)
    if len(s) > hard_trim:
        return s[: hard_trim - 1].rsplit(" ", 1)[0] + "…"
    return s

def _force_numbered_list(s: str) -> str:
    # Split in sinnvolle Sätze/Zeilen und nummerieren
    parts = [p.strip(" -•\t") for p in re.split(r"[.\n]\s+", s) if p.strip()]
    parts = [p for p in parts if len(p) > 0]
    if not parts:
        return s
    return "\n".join(f"{i+1}. {p}" for i, p in enumerate(parts))

def _clamp_citations(s: str, max_n: int) -> str:
    # Erlaube nur Zitate [1..max_n]; entferne andere oder reduziere sie
    def repl(m: re.Match) -> str:
        n = int(m.group(1))
        if 1 <= n <= max_n:
            return f"[{n}]"
        return ""  # drop unknown refs
    return re.sub(r"\[(\d+)]", repl, s)
