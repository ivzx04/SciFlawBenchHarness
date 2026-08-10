from smolagents import Tool
from tools.base import WrappedTool
from tools.definitions import tool_registry
from core.events import EventWatcher


class FakeSearchTool(Tool):
    name = "fake_search"
    description = "deterministic fake search for tests"
    inputs = {"query": {"type": "string", "description": "search query"}}
    output_type = "string"

    def forward(self, query: str) -> str:
        return f"fake results for: {query}"


tool_registry.register("fake_search")(
    lambda watcher: WrappedTool(wrapped_tool=FakeSearchTool(), watcher=watcher)
)
