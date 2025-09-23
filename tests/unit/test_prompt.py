import rag.prompt as p
import random
import uuid
from dataclasses import dataclass


FAKE_QUESTION: str = "What to do in an emergency?"

@dataclass
class FakePromptOptions:
    language: str = "en"
    style: str = "steps"
    max_context_chars: int = 4000
    cite: bool = True
    require_citations: bool = True

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


def test_build_pormpts():
    opts = FakePromptOptions()
    hits = make_fake_hits_custom_chunker(3)

    system, user = p.build_prompts(FAKE_QUESTION, hits, opts)
    print(f"UESER: \n {user}")

    assert 1 == 0
