from tools.base import WrappedTool
from tools.custom import JsonFinalAnswerTool, CalculatorTool, CurrentTimeTool

from core.registry import Registry

from typing import List

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

@tool_registry.register("json_answer_tool")
def make_json_formatting_tool(watcher, required_fields: List[str]=[]) -> WrappedTool:
    return WrappedTool(wrapped_tool=JsonFinalAnswerTool(required_keys=required_fields), watcher=watcher)

@tool_registry.register("current_time")
def make_current_time_tool(watcher) -> WrappedTool:
    return WrappedTool(wrapped_tool=CurrentTimeTool(),watcher=watcher)
