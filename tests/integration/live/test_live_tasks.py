from core.config import ModelConfig
from core.tasks import TaskDef, run_task

import os 
import json
import pytest
import multiprocessing as mp
from pathlib import Path



@pytest.mark.live
@pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"),
        reason="an api key is required to hit the real api"
        )
def test_run_task_with_real_open_ai_agent(tmp_path):
    task_file = tmp_path / "tasks.jsonl"
    task_file.write_text(
    '{"task_id": 1, "task": "What year was the Eiffel Tower completed, and who was the chief engineer credited with the project?", "agent_id": "default_agent", "tools": ["web_search"]}'
    )

    model=ModelConfig(
            provider="litellm", model_id="openai/gpt-5.4-nano-2026-03-17",
            api_base="http://131.220.150.230:8080", api_key_env="OPENAI_API_KEY"
            )

    with open(task_file, "r") as f:
        raw_task = json.load(f)
        taskdef = TaskDef(**raw_task)

    log_path = tmp_path / "logs"
    queue = mp.Queue()

    run_task(taskdef, model, log_path, queue)

    data = json.loads((log_path / f"{taskdef.task_id:03d}.json").read_text())

    assert data["success"] is True
