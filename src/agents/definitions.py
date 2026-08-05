from core.registry import Registry

from tools.definitions import tool_registry

from pydantic import BaseModel
from pathlib import Path
from typing import Type, List, Dict

agent_registry = Registry("agent_descriptions")

class AgentDef(BaseModel):
    """
    Holds the necessary information to provision an agent and is sourced from one of our presets specified as a task
    config
    """
    name: str
    prompt_path: Path
    tools: List[str]
    children: List["AgentDef"] | None = None
    parent: "AgentDef | None" = None
    max_steps: int = 50

# default agent definition
DEFAULT_AGENT_DEF = AgentDef(
            name = "default agent",
            prompt_path = Path("prompts/default.yaml"),
            tools = tool_registry.names(),
            )
            

agent_registry.register("default_agent")(lambda: DEFAULT_AGENT_DEF)
