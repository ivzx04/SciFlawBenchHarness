import os
from pathlib import Path
from typing import Literal, List

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, PrivateAttr, model_validator

class ModelConfig(BaseModel):
    """
    class which stores all the information needed to provision a model (gets read from the config)

    also acts as a typing mechanism thoruhg pydantic to verify things were correctly specified
    """
    provider: Literal["litellm", "openai_server", "hf_api", "vllm_model", "fake_model"]
    model_id: str
    api_key_env: str
    api_base: str | None = None
    extra_kwargs: dict = Field(default_factory=dict)

    _api_key: str = PrivateAttr()

    @model_validator(mode="after")
    def resolve_api_key(self) -> "ModelConfig":
        """
        Function to get the api_key from the enviornment (needs api_key_env to be speciifed in the config)
        """
        load_dotenv()
        value = os.environ.get(self.api_key_env)
        if not value: 
            raise ValueError(f"Env var '{self.api_key_env}' is not set")
        self._api_key = value
        return self

    @property
    def api_key(self) -> str:
        """
        Method to expose the api key parameter throgh code to classes that have the model config

        Returns (str): the raw api_key
        """
        return self._api_key

class RunConfig(BaseModel):
    """
    class which stores all the information needed to provision a benchmark run (also gets read from the config)
    """
    model: ModelConfig
    task_file: Path 
    log_path: Path = Path("logs/")
    max_concurrent: int = 4         # default max concurrent task running processes

    logging_level: int = 20
    restarting: bool | None = None  # if your restarting everything specify this is true and have the log path be specific


    @field_validator("task_file")
    @classmethod
    def task_path_exists_and_is_jsonl(cls, v: Path) -> Path:
        """
        just checks that the task_file field exists, and is a valid jsonl file
        """
        if not v.is_file():
            raise ValueError(f"Tasks file not found: {v}")
        if not v.suffix == ".jsonl":
            raise ValueError(f"Tasks file not jsonl: {v}")
        return v
