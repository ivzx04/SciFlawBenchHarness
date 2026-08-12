from tools.base import WrappedTool
from tools.calculator import CalculatorTool

from core.registry import Registry

from smolagents import  DuckDuckGoSearchTool, WikipediaSearchTool, VisitWebpageTool

# tool registry global object that will keep track of string -> factory mappings for building our tools
tool_registry = Registry("Tool")

@tool_registry.register("web_search")
def make_web_search_tool(watcher) -> WrappedTool:
    return WrappedTool(wrapped_tool=DuckDuckGoSearchTool(), watcher=watcher)

@tool_registry.register("wikipedia_search")
def make_wiki_search_tool(watcher) -> WrappedTool:
    return WrappedTool(wrapped_tool=WikipediaSearchTool(), watcher=watcher)


@tool_registry.register("visit_webpage")
def make_visit_webpage_tool(watcher) -> WrappedTool:
    return WrappedTool(wrapped_tool=VisitWebpageTool(), watcher=watcher)

@tool_registry.register("calculator")
def make_calculator_tool(watcher) -> WrappedTool:
    return WrappedTool(wrapped_tool=CalculatorTool(), watcher=watcher)


