import pytest

from core.events import *
from tools.base import WrappedTool
from models.base import WrappedModel

from smolagents import Tool, Model
from smolagents.models import ChatMessage, MessageRole


def test_emit_calls_sink_with_event():
    captured: list[AgentEvent] = []
    watcher = EventWatcher(task_id=1, sink=captured.append)

    watcher._emit(EventType("tool_call_start"), {"name": "web_search"})

    assert len(captured) == 1
    assert captured[0].task_id == 1
    assert captured[0].payload["name"] == "web_search"


def test_watcher_call_with_fake_tool():

    class FakeSearchTool(Tool):
        name = "fake_search"
        description = "a fake search tool for testing"
        inputs = {"query": {"type": "string", "description": "search query"}}
        output_type = "string"

        def forward(self, query: str) -> str:
            return f"results for: {query}"

    captured: list[AgentEvent] = []
    watcher = EventWatcher(task_id=1, sink=captured.append)
    test_tool = WrappedTool(wrapped_tool=FakeSearchTool(), watcher=watcher)

    result = test_tool.forward(query="python testing")

    assert result == "results for: python testing"
    event_types = [e.event_type for e in captured]
    assert event_types == [EventType.ToolCallStart, EventType.ToolCallEnd]
    assert captured[0].payload["kwargs"] == {"query": "python testing"}
    assert captured[1].payload["result"] == "results for: python testing"

def test_watcher_call_with_fake_model():

    class FakeModel(Model):
        def generate(
            self,
            messages,
            stop_sequences=None,
            response_format=None,
            tools_to_call_from=None,
            **kwargs,
        ) -> ChatMessage:
            return ChatMessage(
                role=MessageRole.ASSISTANT,
                content="fake response",
            )

    captured: list[AgentEvent] = []
    watcher = EventWatcher(task_id=1, sink=captured.append)
    test_model = WrappedModel(wrapped_model=FakeModel(), watcher=watcher)

    result = test_model.generate(messages="python testing")

    assert isinstance(result, ChatMessage)
    event_types = [e.event_type for e in captured]
    assert event_types == [EventType.ModelCallStart, EventType.ModelCallEnd]
    assert captured[0].payload["kwargs"] == { "messages": "python testing"}
    assert captured[1].payload["result"].role == MessageRole.ASSISTANT
    assert captured[1].payload["result"].content == "fake response"

            


def test_watcher_records_error_and_reraises():
    captured: list[AgentEvent] = []
    watcher = EventWatcher(task_id=1, sink=captured.append)

    class BrokenTool(Tool):
        name = "broken"
        description = "always fails"
        inputs = {}
        output_type = "string"
        def forward(self):
            raise ValueError("simulated failure")

    test_tool = WrappedTool(wrapped_tool=BrokenTool(), watcher=watcher)

    with pytest.raises(ValueError, match="simulated failure"):
        test_tool.forward()

    assert captured[-1].event_type == EventType.Errored
    assert "simulated failure" in captured[-1].payload["error"]

