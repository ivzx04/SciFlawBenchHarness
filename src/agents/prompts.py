import yaml
from smolagents import PromptTemplates
from pathlib import Path

def load_prompt_templates(path: Path) -> PromptTemplates:
    """
    loads a prompt definiton from yaml into a smolagents PromptTemplate

    Args:
        path (Path): the path to the prompt file (should be in the agents/prompts/ directory)
    """
    base_path = Path(__file__).parent
    full_path = base_path / path
    
    if not full_path.is_file():
        raise FileNotFoundError(
            f"System prompt file not found: {full_path}\n"
            f"Create a SYSTEM.yaml file or pass a custom path to load_system_prompt()."
        )
    with open(full_path, encoding="utf-8") as f:
        templates = yaml.safe_load(f)
    return templates


