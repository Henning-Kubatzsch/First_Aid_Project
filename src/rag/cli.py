# src/rag/cli.py
from __future__ import annotations
import typer, json, os
from rag.generator import simple_answer, load_llm_config, LocalLLM
from rag.embed import SBertEmbeddings
from rag.indexer import HnswIndex
from rag.retriever import Retriever
import time
from scripts.build_index import build_erc_index


app = typer.Typer(help="RAG CLI")

# ===============================
# Commands for document retrieval
# ===============================

@app.command("ingest")
def ingest(
    docs_dir: str = typer.Option("data/docs", "--docs", help="Folder with ERC .txt/.md"),
    out_dir: str  = typer.Option("data/index", "--out", help="Where to store HNSW index"),
    embed_model: str = typer.Option("sentence-transformers/all-MiniLM-L6-v2", "--embed-model"),
    custom_chunker: bool = typer.Option(False, "--custom_chunker", help="uses custom data source format")
):
    build_erc_index(docs_dir=docs_dir, out_dir=out_dir, model_name=embed_model, custom_chunker=custom_chunker)
    typer.echo(f"Index written to {out_dir}")

@app.command("get_retriever_format")
def get_retriever_format(
    question: str = typer.Argument(..., help="User question"),
    config: str = typer.Option("configs/rag.yaml", "--config", "-c"),
    index_dir: str = typer.Option("data/index", "--index"),
    embed_model: str = typer.Option("sentence-transformers/all-MiniLM-L6-v2", "--embed-model"),
    k: int = typer.Option(2, "--k"),
):
    # 1) Load LLM
    llm_cfg = load_llm_config(config)
    llm = LocalLLM(llm_cfg)

    # 2) Load embedder + index
    embedder = SBertEmbeddings(model_name=embed_model)
    # dim = len(embedder.embed_one("probe"))
    index = HnswIndex()
    index.load(index_dir)  # uses header stored during build

    # 3) Retrieve
    retriever = Retriever(embedder, index, k=k)
    docs = retriever.search(question)
    print(docs)



@app.command("ask")
def ask(
    question: str = typer.Argument(..., help="User question"),
    config: str = typer.Option("configs/rag.yaml", "--config", "-c"),
    index_dir: str = typer.Option("data/index", "--index"),
    embed_model: str = typer.Option("sentence-transformers/all-MiniLM-L6-v2", "--embed-model"),
    k: int = typer.Option(2, "--k"),
):
    # 1) Load LLM
    llm_cfg = load_llm_config(config)
    llm = LocalLLM(llm_cfg)

    # 2) Load embedder + index
    embedder = SBertEmbeddings(model_name=embed_model)
    # dim = len(embedder.embed_one("probe"))
    index = HnswIndex()
    index.load(index_dir)  # uses header stored during build

    # 3) Retrieve
    retriever = Retriever(embedder, index, k=k)
    docs = retriever.search(question)

    # 4) Build prompt with context and ask LLM
    context = "\n\n".join(f"[{i+1}] {d['text']}" for i, d in enumerate(docs))
    system = "You are a concise, ERC-aligned training assistant. Answer with short, safe, step-by-step instructions and cite [1], [2] as needed."
    user = f"Context:\n{context}\n\nQuestion:\n{question}"       

    msgs = llm.make_messages(user=user, system=system)
    answer = llm.chat(msgs, max_tokens=llm_cfg.max_tokens)   

    print(answer)

@app.command("llm-stream")
def llm_stream(
    question: str = typer.Argument(..., help="User question"),
    config: str = typer.Option("configs/rag.yaml", "--config", "-c"),
    index_dir: str = typer.Option("data/index", "--index"),
    embed_model: str = typer.Option("sentence-transformers/all-MiniLM-L6-v2", "--embed-model"),
    k: int = typer.Option(2, "--k"),
):
    
    # 1) Load LLM
    llm_cfg = load_llm_config(config)
    llm = LocalLLM(llm_cfg) 

    # 2) Load embedder + index
    embedder = SBertEmbeddings(model_name=embed_model)
    dim = len(embedder.embed_one("probe"))

    index = HnswIndex()
    index.load(index_dir)  # uses header stored during build

    # 3) Retrieve
    retriever = Retriever(embedder, index, k=k)
    docs = retriever.search(question)      

    # 4) Build prompt with context and ask LLM
    context = "\n\n".join(f"[{i+1}] {d['text']}" for i, d in enumerate(docs))   
    system = "give short answers"
    user = f"Context:\n{context}\n\nQuestion:\n{question}"  

    msgs = llm.make_messages(user=user, system=system)

    for tok in llm.chat_stream(msgs):
        print(tok, end="", flush=True)    
    
# ======================================
# Direct commands to LLM -> no retrieval
# ======================================

# using simple_answer creates model each time
@app.command("ask-no-retrieval")
def ask_no_retrieval(
    question: str = typer.Argument(..., help="Prompt to send to the local LLM"),
    config: str = typer.Option("configs/rag.yaml", "--config", "-c"),
):
    system = ("You are a concise, safe training assistant. "
              "Give step-by-step ERC-aligned instructions.")
    out = simple_answer(question, system, config)
    typer.echo(out)

# using simple_answer creates model each time
@app.command("llm-sanity-no-retrieval")
def llm_sanity_no_retrieval(
    question: str = typer.Argument(...),
    config: str = typer.Option("configs/rag.yaml", "--config", "-c"),
):
    system = ("You are a concise, safe training assistant. "
              "Give step-by-step ERC-aligned instructions.")
    out = simple_answer(question, system, config)
    typer.echo(out)

# create model then stream tokens to stdout
@app.command("llm-stream-no-retrieval")
def llm_stream_no_retrieval(
    question: str = typer.Argument(...),
    config: str = typer.Option("configs/rag.yaml", "--config", "-c"),
):
    cfg = load_llm_config(config)
    llm = LocalLLM(cfg)
    msgs = llm.make_messages(
        user=question,
        system="You are a concise ERC training assistant.",
    )
    for tok in llm.chat_stream(msgs):
        print(tok, end="", flush=True)
    print()

if __name__ == "__main__":
    app()
