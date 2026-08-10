from agents.base import AgentDef, build_agent 
from agents.definitions import agent_registry
from core.events import AgentEvent, EventWatcher
from core.config import ModelConfig

import os
import json
import traceback
import dataclasses
import logging
import multiprocessing as mp
from typing import Type, List, Dict, Any
from pathlib import Path

from pydantic import BaseModel

logger = logging.getLogger(__file__)

if os.environ.get("ENABLE_TEST_FAKES")  == "1":
    import tests.fakes.tools
    import tests.fakes.presets


class TaskDef(BaseModel):
    """
    Working definition for tasks to be passed through the runtime manager and dispatched to a task runner 
    (not necessarily for the evaluator itself)

    TODO: ground truth should be passed through here as well to allow for quantatative checks to be run by the 
    task runners upon getting the solutionn to be included in the logs
    """
    task_id: int
    task: str
    agent_id: str
    tools: List[str]

class TaskResult(BaseModel):
    """
    Final result that gets dumped into the log file 

    (FOR NOW: really only gets used in run task but perhaps later we use it for passing around result objects and 
    unloading the tasks i feel its worth keeping it around)
    """
    task_id: int
    task: str
    output: Any
    success: bool
    error: str
    full_trace: List[Dict]
    memory_trace: List[Dict] | None


# TODO: quantatative checks on the task result should **probably** also be done here
def run_task(task: TaskDef, model_conf: ModelConfig, output_dir: Path, res_queue: mp.Queue):
    """
    The target function actually run by the runtime manager to launch subprocesses which complete provision and
    complete the agentic tasks

    Args:
        task (TaskDef): necessary information to run the given task
        model_conf (ModelConfig): information needed to build the model for this task
        output_dir (Path): path to the log directory where the result json file is written
        res_queue (mp.Queue): queue in which to signal that the task has finished running so the runtimme manager can
        clean up

    """
    events: List[AgentEvent] = []
    watcher = EventWatcher(task_id=task.task_id, sink=events.append)

    try:
        built_agent = build_agent(task.agent_id, model_conf, watcher)
        out = built_agent.watcher("agent", built_agent.definition.name, built_agent.agent.run, task.task)
        success = True
        error_str = ""
    except Exception as e: 
        out = None
        success = False
        error_str = traceback.format_exc()
        memory_steps = None
    else:  # if there was no error try to get agent memory
        try:
            memory_steps = built_agent.agent.memory.get_full_steps()
        except Exception:
            memory_steps = None

    result = TaskResult(
            task_id=task.task_id, 
            task=task.task, 
            output=out, 
            success=success,
            error=error_str,
            full_trace=[dataclasses.asdict(event) for event in events],
            memory_trace=memory_steps
            )


    if not output_dir.exists():
        os.mkdir(output_dir)

    temp_file = output_dir / f"{task.task_id:03d}.json.tmp"
    out_file = output_dir / f"{task.task_id:03d}.json"

    with open(temp_file, 'w') as f:
        json.dump(result.model_dump(),f)
    os.rename(temp_file, out_file)
    res_queue.put({"task_id": task.task_id, "success": success})

