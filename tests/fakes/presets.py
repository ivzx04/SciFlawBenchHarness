from agents.base import agent_registry, AgentDef
from core.config import ModelConfig
from pathlib import Path

FAKE_AGENT = AgentDef(
    name="fake_agent",
    prompt_path=Path("prompts/code_agent.yaml"),   # reuse a real prompt template — no need to fake this too
    tools=["fake_search"],
    agent_type="code",
    max_steps=2,
)

agent_registry.register("fake_agent")(lambda: FAKE_AGENT)
