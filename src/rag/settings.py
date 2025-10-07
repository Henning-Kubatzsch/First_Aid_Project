from pathlib import Path
import yaml
from functools import lru_cache
from rag.prompt import PromptOptions 

class Settings:
    def __init__(self, prompt: PromptOptions):
        self.prompt = prompt

def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
    
@lru_cache(maxsize = 1)
def get_settings(cfg_path: str = "configs/rag.yaml") -> Settings:
    data = _load_yaml(Path(cfg_path))
    p = (data or {}).get("prompt", {})
    prompt = PromptOptions(
        language = p.get("language", "en"),
        style = p.get("style", "steps"),
        max_context_chars = p.get("max_content_chars", 4000),
        cite = p.get("cite", True),
        require_citations = p.get("require_citations", "True")
    )
    return Settings(prompt=prompt)

