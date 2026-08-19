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
from typing import Dict, Set, List, Any
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
        logging.basicConfig(level=conf.logging_level)

        logger.info("Initailizing runtime manager for current run")
        self.model_conf = conf.model

        if conf.restarting:
            self.log_path = conf.log_path
        else: 
            self.log_path = conf.log_path / time.strftime("%Y-%m-%d %H:%M:%S")

        self.task_file = conf.task_file
        self.max_concurrent = conf.max_concurrent
        self.task_timeout_s = conf.task_timeout_s


        if not self.log_path.exists():
            os.makedirs(self.log_path)

        self.shared_results_jsonl = self.log_path / "aggregate_results.jsonl"
        self.run_summary_file = self.log_path / "run_summary.log"

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
            for line_num, raw_line in enumerate(f):
                line = raw_line.strip()
                if not line:
                    continue
                try: 
                    task = TaskDef(**json.loads(line))
                except Exception as e:
                    logger.error(f"Failed to load task on line {line_num + 1}: got the following error: {e}")
                    exit(1)

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

        self._drain_remaining()

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
        upon having completed. Adding important results to the shared results file

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

        self._handle_message(msg)


    def _check_timeouts(self): 
        """
        Another function run at the end of the spanwing loop which basically just checks the active processes and kills
        them if they dont complete in the specified amount of seconds. For the moment this waits 15 minutes on any given
        process but this can be configured fairly easily if we find that we need different time scales
        """
        now = time.time()
        to_kill: list[int] = []

        for task_id, entry in self._active.items():
            if now - entry['started'] > self.task_timeout_s:
                entry['proc'].terminate()
                entry['proc'].join(timeout=10) # 10 seconds for the process to clean up after itself 
                if entry['proc'].is_alive():
                    entry['proc'].kill()
                    entry['proc'].join(timeout=5)
                to_kill.append(task_id)
                logger.info(f"Task: {task_id:03d} timed out...")

        # update dictionary state associated with killed tasks
        for task_id in to_kill:
            del self._active[task_id]

    def _handle_message(self, msg: Dict[str, Any]):
        """
        takes a message in and handles logging according to what the message content is 

        Args:
            message (Dict[str, Any]): the message being sent by the subprocess to be logged
        """
        task_id = msg['task_id']
        log = msg["to_log"]

        match msg["kind"]:
            case "task_finished":
                if msg["success"]:
                    logger.info(f"Task: {task_id:03d} completed successfully!")
                else: 
                    err = log["error"]
                    logger.info(f"Task: {task_id:03d} completed exectution with following errors:\n {err} ")
            case "killed":
                logger.info(f"Task: {task_id:03d} reaped. Killed by timeout.")
            case _: 
                logger.info(f"Task: {task_id:03d} finished with undefined state...")


        with open(self.shared_results_jsonl, "a") as f:
            f.write(json.dumps(log)+ "\n")

        with open(self.run_summary_file, "a") as f:
            line = f"[{log['status'].upper():9}] task {log['id']:>4}  {log['time_elapsed']:.1f}s"
            if log["status"] == "success":
                checks = log.get('checks', [])
                passed = sum(int(check['passed']) for check in checks)
                line += f"  Checks:     {passed}/{len(checks)}"
            else:
                line += f"  Last Event: {log.get('last_event', '')}"
            f.write(line + "\n")

    def _drain_remaining(self):
        """
        This function runs after the main loop has been completed and handles draining 
        any remaining results in the result queue (eg. handling logging task info)
        """

        while True: 
            try: 
                msg = self._result_queue.get(timeout=3.0)
            except q.Empty:
                break

            self._handle_message(msg)
        
