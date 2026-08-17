# project modules
from core.config import RunConfig, ModelConfig
from core.tasks import run_task, TaskDef

# stdlib
import os
import json 
import time 
import logging 
import queue as q
import multiprocessing as mp 
from typing import Dict, Set, List
from pathlib import Path

# pip installed
from smolagents import LiteLLMModel, OpenAIServerModel, Model

mp.set_start_method("spawn", force=True) # IMPORTANT: this means it will not just fork the process, which means slightly
                                         # slower start times but ultimately saves from pain when it comes to possible 
                                         # deadlocks with open file descriptors and networking (although im willing to 
                                         # remove if we promise to be careful about not doing any of that stuff with 
                                         # the main process)

logger = logging.getLogger(__file__)

class RuntimeManager:
    """
    This is the class that orchestrates running all of the tasks from the tasklist through the run method. It is
    configured mainly through the config.json file that holds all the necessary information needed to provision a test
    """

    def __init__(self, conf: RunConfig):
        logger.info("Initailizing runtime manager for current run")
        self.model_conf = conf.model

        if conf.restarting:
            self.log_path = conf.log_path
        else: 
            self.log_path = conf.log_path / time.strftime("%Y-%m-%d %H:%M:%S")

        self.task_file = conf.task_file
        self.max_concurrent = conf.max_concurrent


        if not self.log_path.exists():
            os.makedirs(self.log_path)

        self._result_queue = mp.Queue()
        self._active: Dict[int, dict] = {} 
        self._pending = self.load_tasks()
        logger.info("Runtime manager initialized")
    
    def load_tasks(self) -> List[TaskDef]:
        """
        This method loads all of the yet to be completed logs in single run of the harness according to the files in the
        log directory

        Returns: a list of task definitions (see tasks.py for implementation details) that are read from the task file
        specified through the configuration file
        """
        already_done = self.load_completed()
        pending = []

        with open(self.task_file, 'r') as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                task = TaskDef(**json.loads(line))
                if task.task_id not in already_done:
                    pending.append(task)
        return pending


    def load_completed(self) -> Set[int]:
        """
        simple scan of log directory to recover state of completed tasks

        Returns (Set[int]): a set of integers representing completed task ids
        """

        res_dir = self.log_path / "results"
        if not res_dir.is_dir():
            logger.info(f"loaded no completed items from {self.log_path}")
            return set()
        return {int(p.stem) for p in res_dir.glob("*.json")}

    def run(self) -> None:
        """
        This function starts the main loop that launches subprocesses to run tasks. it will try to launch subprocesses
        until its less than the current maximum concurrent and while there are still tasks to be run (in pending).
        """

        while self._pending or self._active: 
            while self._pending and len(self._active) < self.max_concurrent: 
                task = self._pending.pop(0)
                proc = self._spawn_task(
                        task = task,
                        model_conf = self.model_conf,
                        log_path = self.log_path,
                        res_queue = self._result_queue
                        )
                self._active[task.task_id] = {"proc": proc, "started": time.time()}
                logger.info(f"Task id - ({task.task_id:03d}) is now started")

            self._drain_results()
            self._check_timeouts()

    def _spawn_task(self, task: TaskDef, model_conf: ModelConfig, log_path: Path, res_queue: mp.Queue) -> mp.Process:
        """
        simply spawns a subprocess which actually runs the task with the agent setup and model configuraion specified 

        Args: 
            task (TaskDef): defintion of the task (includes the agentic preset to be run)
            model_conf (ModelConfig): configuration struct containing what is needed to provision a fresh model
            log_path (Path): path to the directory containing completed log files
            res_queue (mp.Queue): queue used to track state of active processes and when they finish

        Returns (mp.Process): a process class handler class which will be tracked through the _active queue 
        """
        p = mp.Process(target=run_task, args=(task, model_conf, log_path, res_queue,))
        p.start()
        return p


    def _drain_results(self, timeout:float = 3.0):
        """
        Function run at the end of the spawning loop which basically just checks for finished processes and reaps them 
        upon having completed

        Args:
            timeout (float): amount of seconds to wait while accessing the result queue
        """
        try:
            msg = self._result_queue.get(timeout=timeout)
        except q.Empty:
            return

        # reap the finished process
        task_id = msg["task_id"]
        entry = self._active.pop(task_id, None)
        if entry:
            entry["proc"].join(timeout=5)

        logger.info(f"Task: {task_id:03d} completed successfully!")

    def _check_timeouts(self, timeout_s: float = 60 * 15): # a fifteen minute timeout for a given task
        """
        Another function run at the end of the spanwing loop which basically just checks the active processes and kills
        them if they dont complete in the specified amount of seconds. For the moment this waits 15 minutes on any given
        process but this can be configured fairly easily if we find that we need different time scales

        Args:
            timeout_s (float): timeout in seconds after which a subrpocess task will be automatically reaped
        """
        now = time.time()
        for task_id, entry in self._active.items():
            if now - entry['started'] > timeout_s:
                entry['proc'].terminate()
                entry['proc'].join(timeout=5)
                if entry['proc'].is_alive():
                    entry['proc'].kill()
                del self._active[task_id]
                logger.info(f"Task: {task_id:03d} timed out and got killed")
