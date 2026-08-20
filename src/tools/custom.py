
import sys, json, subprocess, time

from typing import List

from smolagents import Tool

CALC_SCRIPT = """
import sys, json, resource
resource.setrlimit(resource.RLIMIT_CPU, (5,5)) # 5 cpu-second hard cap for the process
resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024,) * 2) # 1 GB memory cap

import sympy
expr = sys.argv[1]
result = sympy.sympify(expr, evaluate=True)
print(json.dumps(str(result)))
"""

class CalculatorTool(Tool):
    name = "calculator"
    description = "Evaluates Mathematical expressions using sympy. returns the simplified result. will error for calculations that are too expensive to calculate (~5 seconds cpu time and 512 MB of memory)"
    inputs = {"expression": {"type": "string", "description": "a sympy compatible math expression less than 500 chars"}}
    output_type = "string"

    def forward(self, expression: str) -> str:
        if len(expression) > 500:
            return "Error: expression too long, likely malformed"

        try:
            proc = subprocess.run( 
                                  [sys.executable, "-c", CALC_SCRIPT, expression], 
                                  capture_output = True, 
                                  text = True, 
                                  timeout = 10
                                  )
        except subprocess.TimeoutExpired:
            return "Error: calculation timed out - Expression too complex to evaluate"

        if proc.returncode != 0:
            return f"Error: could not evaluate expression\n \
                stderr\n: ({proc.stderr.strip()})\n stdout:\n ({proc.stdout.strip()})"

        return json.loads(proc.stdout)
            

class JsonFinalAnswerTool(Tool):
    name = "json_answer_tool"
    description = """Tool for for validating the format of final answers that specify a json format. Returns the json
    string if its valid json containing all required answer fields specified in the task description. Otherwise an error
    string mentioning what went wrong will be returned. (note this tool does NOT actually submit the final answer. any
    final answers here must still be wrapped by a call to the final_answer tool) ALWAYS validate that this tool is
    correctly formatting your proposed answer before submitting a final answer from its result"""

    inputs = {"json_string": {"type": "string", "description": "a json formatted string to be parsed and validated as json"}}
    output_type = "string"

    def __init__(self, required_keys: List[str] = []):
        super().__init__()
        self.required_keys = required_keys


    def forward(self, json_string: str) -> str:
        try:
            parsed = json.loads(json_string)
        except json.JSONDecodeError as e:
            return f"JSONDecodeError: {e}"

        if not isinstance(parsed, dict):
            return f"Error: parsed object must be a Json object, not a string or int "

        missing = [key for key in self.required_keys if key not in parsed] 

        if missing:
            return f"Error: Missing Required Key(s) - {missing}"
        return json_string

class CurrentTimeTool(Tool):
    name = "current_time"
    description = """This tool just returns the current time in case this ever comes into question. returns in the
    following format: %Y-%m-%d %H:%M:%S"""

    inputs = {}
    output_type = "string"

    def forward(self) -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S")
