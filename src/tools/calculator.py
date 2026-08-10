
import sys, json, subprocess 

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
            
