from rag.prompt import build_prompts, _build_context_and_bib, _squash, _system_prompt, _answer_rules, _normalize, _force_numbered_list, _clamp_citations
import random
import uuid
from dataclasses import dataclass
import re


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
    random.seed(0)
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

def make_fake_bib():
    bib = '[1]\n title: first_Aid_instructions.txt\n id: b16b03bae7294d19\n[2]\n title: first_Aid_instructions.txt\n id: 41583717b2f74bf7\n[3]\n title: first_Aid_instructions.txt\n id: 2b50afd3df32498a'
    return bib

def make_test_string():
    test_string = ""



def test_build_pormpts_custom_chunker():
    opts = FakePromptOptions()
    hits = make_fake_hits_custom_chunker(3)

    system, user = build_prompts(FAKE_QUESTION, hits, opts)
    print(f"UESER: \n {user}")
    print(f"SYSTEM: \n {system}")
    assert isinstance(system, str)
    assert isinstance(user, str)
    assert 'Sources' in system
    assert 'Context' in user and 'Question' in user


# TODO: think about how to implements different languages and if it's needed
#def test_biuld_prompts_german_language():
#
#    opts = FakePromptOptions(language="de")
#    hits = make_fake_hits_custom_chunker(3)
#    system, user = p.build_prompts(FAKE_QUESTION, hits, opts)

def test_build_context_respects_max_contest_chars():
    opts = FakePromptOptions(max_context_chars=400)
    hits = make_fake_hits_custom_chunker(3)
    context, bib =_build_context_and_bib(hits, opts.max_context_chars)
    assert isinstance(bib, str)
    assert isinstance(context, str)
    assert ('[1]' in bib) or bib == ""
    assert ('[1]' in context) or context == ""
    assert len(context) < opts.max_context_chars
    # TODO: find a way for testing if we have no bib needed
    assert len(bib) > 0


def test_squash():
    test_string = "This is a test string"
    s_string = _squash(test_string, len(test_string) -1)
    assert len(s_string) < len(test_string)


# TODO: test with and without bib
def test_system_prompt():
    bib = make_fake_bib()
    opst = FakePromptOptions(max_context_chars=400)
    system_prompt = _system_prompt(opst, bib)
    assert system_prompt

# TODO: check for language selection
def test_answer_rules():
    opts = FakePromptOptions(cite=True)
    rules = _answer_rules(opts)
    assert "Cite sources" in rules

    opts = FakePromptOptions(cite=False)
    rules = _answer_rules(opts)
    assert "Cite sources" not in rules

def test_normalize():
    test_string = "First line\r\n\r\nSecond line\rThird line\n\n\nFourth line\n\n\n\nFifth line\r\n"
    res = _normalize(test_string)
    assert '\r' not in res
    assert not re.search(r'\n{3}', res)

def test_force_numbered_list():
    test_string = """
        - •First instruction.  Make sure to \ncheck the environment.
        • Second step: prepare all materials.
        Third step: follow the guidelines carefully
        Fourth step without bullet
        - Fifth step with dash
        • Sixth step with bullet and extra spaces        
        """
    res = _force_numbered_list(test_string)
    assert '8' in res 
    assert '9' not in res

def test_clamp_citations():
    s = "This [1] is a [2] very short [3] test example [4]"
    s = _clamp_citations(s, 3)
    assert '3' in s
    assert not re.search(r'\[4\]', s)