from core.registry import Registry

from tools.definitions import tool_registry

from pydantic import BaseModel
from pathlib import Path
from typing import List, Literal

agent_registry = Registry("agent_descriptions")

class AgentDef(BaseModel):
    """
    Holds the necessary information to provision an agent and is sourced from one of our presets specified as a task
    config
    """
    name: str
    prompt_path: Path
    tools: List[str]
    agent_type: Literal["code", "tool"]
    children: List["AgentDef"] | None = None
    parent: "AgentDef | None" = None
    max_steps: int = 50

# default agent definitions
DEFAULT_CODING_AGENT = AgentDef(
            name = "default code agent",
            prompt_path = Path("prompts/code_agent.yaml"),
            tools = tool_registry.names(),
            agent_type = "code"
            )

DEFAULT_TOOL_AGENT = AgentDef(
            name = "default tool agent",
            prompt_path = Path("prompts/tool_agent.yaml"),
            tools = tool_registry.names(),
            agent_type = "tool"
            )

agent_registry.register("code_agent")(lambda: DEFAULT_CODING_AGENT)
agent_registry.register("tool_agent")(lambda: DEFAULT_TOOL_AGENT)
