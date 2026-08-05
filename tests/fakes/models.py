import time
from smolagents import Model, ChatMessage, MessageRole
import itertools


class ScriptedModel(Model):
    def __init__(self, responses: list[str]):
        super().__init__()
        self._responses = itertools.cycle(responses)   

    def generate( self, messages, stop_sequences=None, response_format=None,
            tools_to_call_from=None, **kwargs,) -> ChatMessage:
        time.sleep(0.5)
        return ChatMessage(role=MessageRole.ASSISTANT, content=next(self._responses))

