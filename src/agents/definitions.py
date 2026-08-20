from core.registry import Registry

from tools.definitions import tool_registry
from tools.base import ToolDef

from pydantic import BaseModel, field_validator
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
    tools: List[ToolDef | str]
    agent_type: Literal["code", "tool"]
    children: List["AgentDef"] | None = None
    parent: "AgentDef | None" = None
    max_steps: int = 40

    @field_validator("tools", mode="before")
    @classmethod
    def normalize_tools(cls, v):
        if not isinstance(v, list):
            return v
        return [{"tool_name": t} if isinstance(t, str) else t for t in v]

# default agent definitions
DEFAULT_CODING_AGENT = AgentDef(
            name = "default code agent",
            prompt_path = Path("prompts/code_agent.yaml"),
            tools = ["web_search", "wikipedia_search", "visit_webpage", "calculator", "current_time"],
            agent_type = "code"
            )

DEFAULT_TOOL_AGENT = AgentDef(
            name = "default tool agent",
            prompt_path = Path("prompts/tool_agent.yaml"),
            tools = ["web_search", "wikipedia_search", "visit_webpage", "calculator", "current_time"],
            agent_type = "tool"
            )

agent_registry.register("code_agent")(lambda: DEFAULT_CODING_AGENT)
agent_registry.register("tool_agent")(lambda: DEFAULT_TOOL_AGENT)
