import json
import multiprocessing as mp

from core.manager import RuntimeManager
from core.config import RunConfig, ModelConfig
from core.tasks import run_task, TaskDef

def setup_basics(tmp_path, monkeypatch):
    import tests.fakes.tools     # import for side effect: registers "fake_search"
    import tests.fakes.presets   # import for side effect: registers "fake_agent"
    monkeypatch.setenv("FAKE_KEY", "x")


def test_run_fake_task(tmp_path, monkeypatch):
    setup_basics(tmp_path, monkeypatch)
    task_file = tmp_path / "tasks.jsonl"
    task_file.write_text(
        '{"task_id": 1, "task": "say hi", "agent_id": "fake_agent", "tools": ["fake_search"]}\n'
    )

    model=ModelConfig(
        provider="fake_model", model_id="fake", api_key_env="FAKE_KEY",
        extra_kwargs={"responses": ["final_answer('done')"]},
    )

    with open(task_file, "r") as f:
        raw_task = json.load(f)
        taskdef = TaskDef(**raw_task)

    log_path = tmp_path / "logs"
    queue = mp.Queue()

    run_task(taskdef, model, log_path, queue)

    data = json.loads((tmp_path / "logs" / f"{taskdef.task_id:03d}.json").read_text())
    assert data["success"] is True


def test_single_task_pipeline(tmp_path, monkeypatch):
    setup_basics(tmp_path, monkeypatch)
    monkeypatch.setenv("ENABLE_TEST_FAKES", "1")

    task_file = tmp_path / "tasks.jsonl"
    task_file.write_text(
        '{"task_id": 1, "task": "say hi", "agent_id": "fake_agent", "tools": ["fake_search"]}\n'
    )

    conf = RunConfig(
        model=ModelConfig(
            provider="fake_model", model_id="fake", api_key_env="FAKE_KEY",
            extra_kwargs={"responses": ["final_answer('done')"]},
        ),
        task_file=task_file,
        log_path=tmp_path / "logs",
        max_concurrent=2,
    )

    RuntimeManager(conf).run()

    data = json.loads((tmp_path / "logs" / "001.json").read_text())
    assert data["success"] is True

def test_full_pipeline(tmp_path, monkeypatch):
    setup_basics(tmp_path, monkeypatch)
    monkeypatch.setenv("ENABLE_TEST_FAKES", "1")

    task_file = tmp_path / "tasks.jsonl"
    task_file.write_text(
        '{"task_id": 1, "task": "say hi", "agent_id": "fake_agent", "tools": ["fake_search"]}\n'
        '{"task_id": 2, "task": "say bye", "agent_id": "fake_agent", "tools": ["fake_search"]}\n'
    )

    conf = RunConfig(
        model=ModelConfig(
            provider="fake_model", model_id="fake", api_key_env="FAKE_KEY",
            extra_kwargs={"responses": ["final_answer('done')"]},
        ),
        task_file=task_file,
        log_path=tmp_path / "logs",
        max_concurrent=2,
    )

    RuntimeManager(conf).run()

    for task_id in (1, 2):
        data = json.loads((tmp_path / "logs" / f"{task_id:03d}.json").read_text())
        assert data["success"] is True


def test_pipeline_with_pressure(tmp_path, monkeypatch):
    setup_basics(tmp_path, monkeypatch)
    monkeypatch.setenv("ENABLE_TEST_FAKES", "1")

    task_file = tmp_path / "tasks.jsonl"
    task_file.write_text(
        '{"task_id": 1, "task": "say hi", "agent_id": "fake_agent", "tools": ["fake_search"]}\n'
        '{"task_id": 2, "task": "say bye", "agent_id": "fake_agent", "tools": ["fake_search"]}\n'
        '{"task_id": 3, "task": "say bye", "agent_id": "fake_agent", "tools": ["fake_search"]}\n'
        '{"task_id": 4, "task": "say bye", "agent_id": "fake_agent", "tools": ["fake_search"]}\n'
        '{"task_id": 5, "task": "say bye", "agent_id": "fake_agent", "tools": ["fake_search"]}\n'
        '{"task_id": 6, "task": "say bye", "agent_id": "fake_agent", "tools": ["fake_search"]}\n'
        '{"task_id": 7, "task": "say bye", "agent_id": "fake_agent", "tools": ["fake_search"]}\n'
    )

    conf = RunConfig(
        model=ModelConfig(
            provider="fake_model", model_id="fake", api_key_env="FAKE_KEY",
            extra_kwargs={"responses": ["final_answer('done')"]},
        ),
        task_file=task_file,
        log_path=tmp_path / "logs",
        max_concurrent=4,
    )

    RuntimeManager(conf).run()

    for task_id in (1, 2,3,4,5,6,7):
        data = json.loads((tmp_path / "logs" / f"{task_id:03d}.json").read_text())
        assert data["success"] is True
