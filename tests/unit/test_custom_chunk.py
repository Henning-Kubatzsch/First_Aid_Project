import re
from rag.custom_chunk import CustomChunker 

TEST_TEXT ="""

**Question:**

* How do I recognize a cardiac arrest?
* What’s the difference between normal and abnormal breathing?
* What should I do if someone suddenly collapses?

**Recognising Cardiac Arrest:**

* Cardiac arrest is likely if a person is **unresponsive** and shows **no normal breathing**.
* Watch for **agonal respiration** (slow, gasping breaths) – treat this as abnormal.
* Brief **seizure-like movements** may occur at onset. If breathing is absent → start CPR immediately.

---

**Question:**

* When should I call emergency services?
* Should I call first or start compressions first?
* How do I get help if I’m alone?

**Calling Emergency Services:**

* Dial **112 (or your local emergency number)** right away if the person is unresponsive and not breathing.
* If alone, use **speakerphone** so you can start CPR while following dispatcher instructions.
* If you must leave to make the call, always **activate EMS first, then return for CPR**.

---
"""


def test_clean_and_split_text():
    chunker = CustomChunker()  
    sections = chunker._clean_and_split_text(TEST_TEXT)
    print("sections in first test #1: ", repr(sections))
    assert isinstance(sections, list)
    assert len(sections) > 2
    for i, item in enumerate(sections):
        assert r'*' not in item

def test_create_section_lists():
    chunker = CustomChunker()
    sections = chunker._clean_and_split_text(TEST_TEXT)
    print("sections in first test: ", repr(sections))
    splitted_sections = chunker._create_section_lists(sections)
    assert len(splitted_sections) == 2
    print("splitted sections: ", repr(splitted_sections))
    for x in splitted_sections:
        for i, item in enumerate(x):
            assert r'\n*' not in item
            assert item.strip()

def test_creation_sections_dict():
    chunker = CustomChunker()
    sections = chunker._clean_and_split_text(TEST_TEXT)
    splitted_sections = chunker._create_section_lists(sections)
    sections_dict = chunker._create_section_dictionary(splitted_sections)
    print("sections_dict: ", repr(sections_dict))
    assert isinstance(sections_dict, dict)
    for i, item in enumerate(sections_dict):
        assert 'questions' in sections_dict[item]
        assert 'tasks' in sections_dict[item]
        assert sections_dict[item]['questions']
        assert sections_dict[item]['tasks']

def test_create_iterable_chunks():
    chunker = CustomChunker()
    sections = chunker._clean_and_split_text(TEST_TEXT)
    splitted_sections = chunker._create_section_lists(sections)
    sections_dict = chunker._create_section_dictionary(splitted_sections)
    iterable_chunks = chunker._create_iterable_chunks(sections_dict)
    assert isinstance(iterable_chunks, list)
    for i, item in enumerate(iterable_chunks):
        assert 'question' in item
        assert 'text' in item