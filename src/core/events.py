import time
import traceback

from dataclasses import dataclass
from typing import Type, List, Dict, Any, Callable, Literal
from enum import Enum

class EventType(str, Enum):
    """
    Enum used to track the events were interesed (listed down below)
    """
    ToolCallStart = "tool_call_start"
    ToolCallEnd = "tool_call_end"
    ModelCallStart = "model_call_start"
    ModelCallEnd = "model_call_end"
    AgentStart = "agent_call_start" 
    AgentEnd = "agent_call_end" 
    Errored = "error" 


@dataclass
class AgentEvent:
    """
    dataclass containing the full information captured by our agent events listed above. 
    """
    event_type: EventType 
    task_id: int
    payload: Dict[str, Any]
    timestamp: float


class EventWatcher:
    """
    A watcher class which wraps around all agent, tool, and model calls which will basically just store a bunch of agent
    events into the sink (function) its given 
    """
    def __init__(self, task_id: int, sink: Callable):
        self.task_id = task_id
        self._sink = sink

    def _emit(self, event_type: EventType, payload: Dict[str, Any]):
        """
        Hidden method  used in the call which makes the dataclass that gets stored in the sink and actually pushes it 
        through to the sink

        Args:
            event_type (EventType): enum value specifying what kindo of event just took place
            payload (Dict[str, Any]): the actually interesting data associated with this event
        """
        ev = AgentEvent(event_type=event_type, task_id=self.task_id, payload=payload, timestamp = time.time()) 
        self._sink(ev)

    def __call__(self, kind: Literal['agent', 'model', 'tool'], name: str, fn: Callable, *args, **kwargs) -> Any:
        """
        the wrapper endpoint through which you can log one of these events, basically allows a passthrough of any of the
        event functions we are interested in and stores all the information we need to know about how it was used in the
        sink via the _emit call

        Args:
            kind (Literal): one of the literals listed above representing the differnt kinds of things were interested
            in
            name (str): name of the tool, model, agent etc were interesed in calling
            fn (Callable): the function to be run
            args: args to be passed through to the run function
            kwargs: kwargs to be passed through to the run function

        Returns (Any): result of the wrapped function
        """
        start_payload = kwargs.pop("start_payload", None)
        start_load = start_payload if start_payload is not None else {"args": args, "kwargs": kwargs}
        self._emit(event_type=EventType(f"{kind}_call_start"), payload={"name": name, **start_load})
        try: 
            result = fn(*args, **kwargs)
            self._emit(event_type=EventType(f"{kind}_call_end"), payload={"name": name, "result": result})
            return result
        except Exception as e: 
            self._emit(event_type=EventType(f"error"), payload={"name": name, "error": traceback.format_exc()})
            raise



