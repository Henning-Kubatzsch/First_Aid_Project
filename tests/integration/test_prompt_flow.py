# tests/test_prompt_flow.py
import os
import re
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List
import random
import uuid

import pytest

# import typs/ functions from module
from src.rag.prompt import (
    PromptOptions,
    _build_context_and_bib,
    _system_prompt,
    _answer_rules,
)

ARTIFACT_DIR = os.path.join("tests", "artifacts")
ARTIFACT_FILE = os.path.join(ARTIFACT_DIR, "prompt_flow.md")
FAKE_QUESTION: str = "What to do in an emergency?"

# --- Tracer / Recorder ---
class TypeTracer:
    def __init__(self):
        self.rows: List[Dict[str, str]] = []

    def _preview(self, v: Any) -> str:
        try:
            if v is None:
                return "None"
            if is_dataclass(v):
                return repr(asdict(v))
            s = repr(v)
            # entferne Zeilenumbrüche und kürze
            s = re.sub(r"\s+", " ", s).strip()
            #if len(s) > 180:
            #    s = s[:180] + "…"
            return s
        except Exception as e:
            return f"<preview error: {e}>"

    def record(self, step: str, namespace: Dict[str, Any], keys=None):
        """
        step: label z.B. "after_context"
        namespace: dict, z.B. locals() or a dict of selected vars
        keys: optional list of keys to record; default: all keys in namespace
        """
        keys = keys or list(namespace.keys())
        for k in keys:
            if k.startswith("_"):  # skip private variables
                continue
            if k not in namespace:
                continue
            v = namespace[k]
            tname = type(v).__name__
            preview = self._preview(v)
            self.rows.append({"step": step, "variable": k, "type": tname, "preview": preview})

    def to_markdown(self) -> str:
        if not self.rows:
            return "Keine aufgezeichneten Variablen."
        # Header
        md = [
            "# Prompt flow variable types",
            "",
            "| Step | Variable | Type | Preview |",
            "|------|----------|------|---------|",
        ]
        for r in self.rows:
            step = r["step"].replace("|", "\\|")
            var = r["variable"].replace("|", "\\|")
            t = r["type"].replace("|", "\\|")
            p = r["preview"].replace("|", "\\|")
            md.append(f"| {step} | {var} | {t} | {p} |")
        md.append("")  # trailing newline
        return "\n".join(md)

# --- The test that runs the flow and writes the artifact ---
def ensure_artifact_dir():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)

def make_fake_hits_custom_chunker(n=2):
    """Create fake hits in the same format as retriever.search returns."""
    fake_texts = [
        [
            "Look for chest movement, listen for breathing sounds, and feel for air on your cheek.",
            "Take no more than 10 seconds to decide.",
            "If breathing is absent or abnormal (agonal), start CPR immediately.",
        ],
        [
            "Continue compressions until EMS arrives, an AED instructs otherwise, or another trained rescuer takes over.",
            "Stop only if the person shows clear signs of life (normal breathing, movement).",
            "If exhaustion prevents continuation, seek immediate replacement.",
        ],
        [
            "Call emergency services immediately.",
            "Ensure the environment is safe before approaching the patient.",
            "Do not leave the person unattended unless absolutely necessary.",
        ],
    ]
    hits = []
    for i in range(n):
        hits.append({
            "text": fake_texts[i % len(fake_texts)],   # rotate through sample chunks
            "meta": {
                "id": uuid.uuid4().hex[:16],          # random id
                "source": "first_Aid_instructions.txt"
            },
            "score": round(random.random(), 6)        # random float 0..1
        })
    return hits



@pytest.mark.integration
def test_generate_prompt_flow_table():
    """
    Runs the main prompt assembly steps with sample input and records
    variable types & previews into a markdown artifact.
    """
    tracer = TypeTracer()

    # Example Input
    sample_hits = make_fake_hits_custom_chunker(3)

    # 0) entry
    opts = PromptOptions(language="en", style="steps", cite=True)
    tracer.record(
        "entry", 
        {
            "question": FAKE_QUESTION, 
            "sample_hits": sample_hits, 
            "opts": opts
        }, 
        keys=["question", "sample_hits", "opts"]
    )

    # 1) Context + bibliography
    context, bib = _build_context_and_bib(sample_hits, max_chars=opts.max_context_chars)
    tracer.record("after_build_context_and_bib", locals(), keys=["context", "bib"])

    # 2) System message
    system = _system_prompt(opts, bib)
    tracer.record("after_system_prompt", locals(), keys=["system"])

    # 3) User message (simulate both cite True/False branches)
    user_with_cite = f"Context:\n{context}\n\nQuestion:\n{FAKE_QUESTION}\n\nAnswer rules:\n{_answer_rules(opts)}"
    tracer.record("after_user_message_with_cite", locals(), keys=["user_with_cite"])

    user_without_cite = f"Context:\n{context}\n\nQuestion:\n{FAKE_QUESTION}\n\nAnswer rules:\n{_answer_rules(opts, cite=False)}"
    tracer.record("after_user_message_without_cite", locals(), keys=["user_without_cite"])

    # 4) Optionally test postprocess example and record
    # (import postprocess_answer if you want to trace its in/out)
    # from src.rag.prompt import postprocess_answer
    # raw_answer = "1. Do something [3]\n2. Do other"
    # post = postprocess_answer(raw_answer, num_sources=len(sample_hits), opts=opts)
    # tracer.record("after_postprocess", locals(), keys=["raw_answer", "post"])

    # Write artifact
    ensure_artifact_dir()
    md = tracer.to_markdown()
    with open(ARTIFACT_FILE, "w", encoding="utf-8") as fh:
        fh.write(md)

    # Make the test assert something trivial so it doesn't get marked xfail
    assert os.path.exists(ARTIFACT_FILE), "Artifact not created"
