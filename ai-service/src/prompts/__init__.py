import json
from pathlib import Path
from typing import Dict, Any

PROMPTS_DIR = Path(__file__).parent / "prompts"

def load_prompt(name: str) -> Dict[str, Any]:
    """Load a prompt template from JSON file."""
    prompt_file = PROMPTS_DIR / f"{name}.json"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt template not found: {name}")
    
    with open(prompt_file) as f:
        return json.load(f)

def render_prompt(template: str, **kwargs) -> str:
    """Render a prompt template with variables."""
    return template.format(**kwargs)
