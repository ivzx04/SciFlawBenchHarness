from core.events import EventWatcher
from core.config import ModelConfig

import logging
from typing import Any


from smolagents import Model, OpenAIServerModel, LiteLLMModel

class WrappedModel(Model):
    """
    A wrapper around the basic model class that smolagents uses which is connected to an event watcher that logs what it
    gets used for 
    """
    def __init__(self, wrapped_model: Model, watcher: EventWatcher):
        super().__init__()

        self._wrapped = wrapped_model
        self._watcher = watcher

    def generate(self, *args, **kwargs):
        """
        the exposed generate function so that smolagents knows how to use this (wrapped with the watcher so we can get
        the input/results out as well)
        """
        return self._watcher("model", 
                            getattr(self._wrapped, "model_id", self._wrapped.__class__.__name__),
                             self._wrapped.generate, 
                             *args, 
                             **kwargs)

def build_model(conf: ModelConfig, watcher: EventWatcher) -> WrappedModel:
    """
    builds a wrapped model from the provided model config

    Args:
        conf (ModelConfig): configurtion needed to provision the model instance 
        watcher (EventWatcher): provided Event watcher which wraps around all model calls and records inputs/outputs

    Returns (WrappedModel): wrapped model object to be used by the smolagent
    """

    match conf.provider.lower():
        case "litellm":
            import litellm
            litellm.suppress_debug_info = True

            model = LiteLLMModel(
                    model_id = conf.model_id,
                    **conf.extra_kwargs
                    )
        case "openai_server":
            model = OpenAIServerModel(
                    model_id = conf.model_id,
                    api_base = conf.api_base,
                    api_key = conf.api_key,
                    **conf.extra_kwargs
                    )
        case "hf_api":
            raise NotImplementedError("HF_API NOT YET SUPPORTED")
        case "fake_model": # this branch is only for testing
            from tests.fakes.models import ScriptedModel
            model = ScriptedModel(["message 1", "message 2", "message 3", "finished('final_ans')"] )
        case _: 
            raise ValueError(f"Got an unsupported model Provider: {conf.provider}")

    return WrappedModel(wrapped_model=model, watcher=watcher)


