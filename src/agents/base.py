from core.config import ModelConfig
from core.events import EventWatcher

from agents.prompts import  load_prompt_templates
from agents.definitions import AgentDef, agent_registry
from models.base import  build_model
from tools.base import  ToolDef
from tools.definitions import  tool_registry

from dataclasses import dataclass
from pathlib import Path
from typing import List

from smolagents import ToolCallingAgent, CodeAgent, Tool, LogLevel


@dataclass
class BuiltAgent:
    """
    class that just holds all of the information about a provisioned agent / agentic system for ease of passing around
    later
    """
    watcher: EventWatcher
    agent: CodeAgent | ToolCallingAgent
    definition: AgentDef


# TODO: make this thing work for multi agent setups via specifying children and parents
def build_agent(agent_id: str , model_conf: ModelConfig, watcher: EventWatcher, extra_tools: List[ToolDef | str]) -> BuiltAgent:
    """
    builds an agent from the specified agent_id and model conf along with the associated watcher class
    note this builds all of its tools and its model configuration here 

    Args:
        agent_id (str): string specifying the agent / agentic setup to be built 
        model_conf (ModelConfig): description of what is needed to build the model associated with this agent
        watcher (EventWatcher): the watcher associated with this agent, its model instancce and its tools

    """
    model = build_model(model_conf, watcher)
    definition = agent_registry.create(agent_id)
    tools = [tool_registry.create(t.tool_name, watcher=watcher, **t.kwargs) for t in definition.tools + extra_tools] # later add multi agent support [child.to_tool() for child in definition.children],
    prompts = load_prompt_templates(definition.prompt_path)

    if definition.agent_type == "code":
        agent = CodeAgent(
                tools=tools, 
                model=model,
                prompt_templates=prompts, 
                max_steps=definition.max_steps, 
                verbosity_level=LogLevel.OFF
                )
    else:
        agent = ToolCallingAgent(
                tools=tools, 
                model=model,
                prompt_templates=prompts, 
                max_steps=definition.max_steps, 
                verbosity_level=LogLevel.OFF
                )

    return BuiltAgent(
            watcher=watcher,
            agent=agent,
            definition=definition,
            )
