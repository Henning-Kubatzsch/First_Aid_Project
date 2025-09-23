# Setup Guide

## 1. Clone Project and Set Python Version

1. Clone the project from your Git repository:    

```bash
git clone <your-repo-url>
cd <project-folder>
```

2. Set the local Python version using **pyenv**:    

```bash
pyenv local 3.11.9
```

---

## 2. Set Up Poetry Environment

1. Configure Poetry to use the correct Python version:    

```bash
poetry env use 3.11.9
```

2. Install project dependencies:    

```bash
poetry install
```

> Note: This will create a virtual environment in your project folder if your `poetry.toml` is configured with `[virtualenvs] in-project = true`.

---

## 3. Add First Aid Instruction Document

Copy your Resuscitation FAQ document(s) into the `data/docs` folder:

```bash
mkdir -p data/docs   # create the folder if it doesn't exist
cp path/to/your/Resuscitation_FAQ.txt data/docs/
```

> You can add multiple documents if needed.

---

## 4. Set Up Local LLM

1. **Install Hugging Face Hub** (compatible version):    

```bash
poetry add huggingface_hub@^0.23.0
```

2. **Activate the Poetry virtual environment**:    

```bash
source .venv/bin/activate
```

3. **Go to the models directory**:    

```bash
mkdir -p models     # create the folder if it doesn't exist
cd models
```

4. **Download the Qwen2.5 model** from [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF)

> You may need a Hugging Face account and must log in via the terminal:

```bash
huggingface-cli login
```

Then download the model:

```bash
huggingface-cli download Qwen/Qwen2.5-3B-Instruct-GGUF \
    qwen2.5-3b-instruct-q4_k_m.gguf \
    --local-dir . \
    --local-dir-use-symlinks False
```

> **Note:** You can change the model filename in `configs/rag.yaml` if needed.

5. **Return to the project root**:    

```bash
cd ..
```
