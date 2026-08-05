import json
import time
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from core.manager import RuntimeManager
from core.config import RunConfig, ModelConfig


EXAMPLE_TASK1_STRING = '{ "task_id": 1, "task": "Find for me what is the meaning of life, the universe, and everything.", "agent_id": "default", "ground_truth": 42, "tools": ["search"], "failure_modes": { "quantitative": { "correctness": true, "correct_tool_calls": false, "code_safety": false, "robustness_against_adversarial_inputs": false, "time_efficiency": false, "sycophancy":false }, "qualitative": { "planning": false, "reasoning": false, "uncertainty_awareness": true, "aesthetic_quality": false, "lost_context_on_multi_agent_tasks": false, "implicit_domain_knowledge": true } } }'
EXAMPLE_TASK2_STRING = '{ "task_id": 2, "task": "research tomatoes for me and provide 5 facts with sources", "agent_id": "default", "ground_truth": 42, "tools": ["search"], "failure_modes": { "quantitative": { "correctness": true, "correct_tool_calls": false, "code_safety": false, "robustness_against_adversarial_inputs": false, "time_efficiency": false, "sycophancy":false }, "qualitative": { "planning": false, "reasoning": false, "uncertainty_awareness": true, "aesthetic_quality": false, "lost_context_on_multi_agent_tasks": false, "implicit_domain_knowledge": true } } }'


def make_run_config(tmp_path: Path, task_file_content: str) -> RunConfig:
    task_file = tmp_path / "tasks.jsonl"
    task_file.write_text(task_file_content)
    return RunConfig(
        model=ModelConfig(provider="litellm", model_id="fake", api_key_env="FAKE_KEY"),
        task_file=task_file,
        log_path=tmp_path / "logs",
        max_concurrent=2,
    )

def test_load_tasks_parses_all_lines(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_KEY", "x")
    conf = make_run_config(tmp_path, f'{EXAMPLE_TASK1_STRING}\n{EXAMPLE_TASK2_STRING}\n')
    manager = RuntimeManager(conf)

    assert [t.task_id for t in manager._pending] == [1, 2]


def test_load_tasks_skips_blank_lines(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_KEY", "x")
    conf = make_run_config(tmp_path, f'{EXAMPLE_TASK1_STRING}\n\n\n{EXAMPLE_TASK2_STRING}\n')
    manager = RuntimeManager(conf)

    assert len(manager._pending) == 2


def test_load_tasks_excludes_already_completed(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_KEY", "x")
    conf = make_run_config(tmp_path, f'{EXAMPLE_TASK1_STRING}\n{EXAMPLE_TASK2_STRING}\n')

    results_dir = conf.log_path / "results"
    results_dir.mkdir(parents=True)
    (results_dir / "001.json").write_text("{}")

    manager = RuntimeManager(conf)

    assert [t.task_id for t in manager._pending] == [2]

def test_load_completed_returns_empty_set_when_no_results_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_KEY", "x")
    conf = make_run_config(tmp_path, f'{EXAMPLE_TASK1_STRING}\n')
    manager = RuntimeManager(conf)

    assert manager.load_completed() == set()


def test_load_completed_reads_task_ids_from_result_filenames(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_KEY", "x")
    conf = make_run_config(tmp_path, f'{EXAMPLE_TASK1_STRING}\n')

    results_dir = conf.log_path / "results"
    results_dir.mkdir(parents=True)
    (results_dir / "001.json").write_text("{}")
    (results_dir / "002.json").write_text("{}")

    manager = RuntimeManager(conf)

    assert manager.load_completed() == {1, 2}

def test_drain_results_frees_active_slot(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_KEY", "x")
    conf = make_run_config(tmp_path, f'{EXAMPLE_TASK1_STRING}\n')
    manager = RuntimeManager(conf)

    fake_proc = MagicMock()
    manager._active[1] = {"proc": fake_proc, "started": time.time()}
    manager._result_queue.put({"task_id": 1, "success": True})

    manager._drain_results(timeout=1.0)

    assert 1 not in manager._active
    fake_proc.join.assert_called_once()


def test_drain_results_returns_on_empty_queue_without_blocking_forever(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_KEY", "x")
    conf = make_run_config(tmp_path, f'{EXAMPLE_TASK1_STRING}\n')
    manager = RuntimeManager(conf)

    manager._drain_results(timeout=0.1)   # nothing on queue — should return promptly, not hang

    assert manager._active == {}
