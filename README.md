# MR First Aid Training Agent

![Project preview](<ChatGPT Image 19. Aug. 2025, 16_24_51.png>)

🚑 **Project Idea**
A **local, offline intelligent training agent** for **First Aid and resuscitation**.
Long-term vision: an **interactive Mixed Reality (MR)** environment (Quest 3, multi-user) where trainees practice according to **ERC (European Resuscitation Council) guidelines**.
A pedagogical agent, powered by **RAG (Retrieval-Augmented Generation)** and **Agentic RAG**, guides users step by step and adapts in real time.

---

## 🌍 Vision

1. **Local & Offline**

   * Runs on local hardware (MacBook M1 Pro → later Meta Quest 3).
   * No cloud services → private, portable, resilient.

2. **Pedagogical Agent**

   * Trainees ask: *“What should I do next?”*
   * Answers grounded in ERC guidance and tracked progression (ambulance called, CPR started, AED used, …).
   * Later: integrate physiological parameters from a **resuscitation dummy** (blood pressure, compression depth, O₂ saturation) for adaptive feedback.

3. **Agentic RAG**

   * Beyond retrieval: the agent **decides how to react**, evaluates context, and provides next-step instructions.
   * Systematically test chunking, data formatting, and model sizes for clarity and effectiveness.

---

## 🛣️ Development Phases (Roadmap)

**Phase 1 – Local RAG baseline (current)**

* Run a simple offline RAG system on Mac M1 Pro.
* ERC guidelines as knowledge base.
* Local LLM only (e.g., Qwen GGUF via `llama-cpp-python`).
* Conversational CLI with progression tracking.

**Phase 2 – Graph-based progression**

* Model the resuscitation process with LangGraph or a custom state machine.
* Natural-language actions update the progression state.

**Phase 3 – Agentic RAG evaluation**

* Clean/tune ERC text (chunking).
* Test small local LLMs for instruction quality.
* Benchmark clarity and correctness.

**Phase 4 – Standalone Quest 3 deployment**

* Fully local execution on-device.
* Voice input and agent speech output in MR.

**Phase 5 – DummyStation integration**

* Stream real-time parameters from a resuscitation dummy.
* Agent adapts dynamically (e.g., compression depth too shallow → corrective feedback).

---

## ⚙️ Getting Started

### Prerequisites

* macOS on Apple Silicon (tested on M1 Pro)
* Python 3.11+
* [Poetry](https://python-poetry.org/)
* Local LLM runtime (e.g., `llama-cpp-python`) and a compatible **GGUF** model
* (Server) `uvicorn`, `fastapi`

### Install

```bash
git clone <this-repo>
cd <this-repo>
poetry install
```

Place your (paraphrased) ERC-based summaries in the docs directory you plan to index (see **Create Index**).

---

## 🧭 Navigate the Project

### Create Index

Build or rebuild the vector index:

```bash
poetry run rag ingest
```

To use other parameters, modify the `ingest` method in `src/rag/cli.py`.

| parameter     | description                  |
| ------------- | ---------------------------- |
| `docs_dir`    | where to find source docs    |
| `out_dir`     | where to write the index     |
| `embed_model` | which embedding model to use |

---

### Interact **without** a server

*(creates a new model instance each run)*

Generic form:

```bash
poetry run rag <module> [options] "your question"
```

Common options:

* `-c configs/rag.yaml` – config for the LLM/RAG
* `--index data/index` – path to the retriever index

Available modules:

| **module**                | **required arg** | **RAG** |
| ------------------------- | ---------------- | ------- |
| `ask`                     | `str`            | yes     |
| `llm-stream`              | `str`            | yes     |
| `ask-no-retrieval`        | `str`            | no      |
| `llm-sanity-no-retrieval` | `str`            | no      |
| `llm-stream-no-retrieval` | `str`            | no      |

Examples:

```bash
# Streaming RAG with config + index
poetry run rag llm-stream -c configs/rag.yaml --index data/index \
  "What is the rhythm or speed for applying CPR?"

# Quick sanity check (no retrieval), streaming
poetry run rag llm-stream-no-retrieval "Put your question here"
```

---

### Start & Use Local Server

#### Terminal 1 – server

Runs `async def lifespan(app: FastAPI)` in `src/rag/server.py`:

```bash
poetry run uvicorn rag.server:app --host 127.0.0.1 --port 8000 --reload
```

#### Terminal 2 – client

##### Healthcheck:

```bash
curl http://127.0.0.1:8000/health
# -> {"ok": true}
```

##### RAG query (retrieval + generation):

At the moment, the server’s **streaming endpoint** for RAG queries is not functional.
This means the following request will not work as expected:

```bash
curl -N -X POST http://127.0.0.1:8000/rag \
  -H "Content-Type: application/json" \
  -d '{"q": "What should I do next for an unresponsive adult?"}'
```

Instead, you should use the **non-streaming endpoint**, which is currently supported:

```bash
curl -N -X POST http://127.0.0.1:8000/rag_once \
  -H "Content-Type: application/json" \
  -d '{"q": "What should I do next for an unresponsive adult?"}'
```

Support for streaming will be added in a later version. For now, please rely on `/rag_once` for retrieval + generation queries.


| Option                                                           | Meaning                                                | Why it matters here                                                  |
| ---------------------------------------------------------------- | ------------------------------------------------------ | -------------------------------------------------------------------- |
| `-N`                                                             | **Disable buffering** (no output buffering in `curl`). | Ensures you see tokens immediately, instead of buffered all at once. |
| `-X POST`                                                        | **HTTP method POST**.                                  | The `/rag` endpoint expects POST, not GET.                           |
| `http://127.0.0.1:8000/rag`                                      | **Target URL**.                                        | Local FastAPI server running on port 8000.                           |
| `-H "Content-Type: application/json"`                            | **Set request header**.                                | Tells the server the body is JSON.                                   |
| `-d '{"q": "What should I do next for an unresponsive adult?"}'` | **Request body (data)**.                               | Provides the input (`q`) that your RAG system should answer.         |

shorter way

```bash
curl --json '{"q":"What to do when arriving at an accident?"}' http://127.0.0.1:8000/rag

```

---

## ⚠️ Disclaimer

This project is **for training and research purposes only**.
It does **not** replace certified medical training or real emergency protocols.
Always follow official ERC guidelines and seek certified instruction.

### Legal Notice

This project uses **paraphrased and simplified summaries** inspired by the recommendations of the **European Resuscitation Council (ERC)**.
It does **not** include or redistribute official ERC guideline texts.
For authoritative and up-to-date information, consult the official ERC publications at [https://erc.edu](https://erc.edu).

---

## 📦 Third-Party Licenses

This project depends on several open-source libraries (MIT, Apache-2.0, BSD-3-Clause, PSF).
For details, see [THIRD\_PARTY\_LICENSES.md](./THIRD_PARTY_LICENSES.md).

---

## Notes & Gotchas (read this)

* Local models can hallucinate. Keep prompts concrete and verify outputs against ERC sources.
* Smaller GGUF models run fast on M-series CPUs/Metal but may reduce accuracy—benchmark before training sessions.
* Index quality beats model size: clean, focused chunks outperform noisy text dumps.
* Keep the project **offline** to preserve privacy; avoid dropping in cloud SDKs by habit.
