from tools.custom import CalculatorTool

def test_simple_calculation():
    calc = CalculatorTool()

    result = calc.forward("10 + 10")


    assert result == "20"

def test_simple_integral():
    calc = CalculatorTool()

    result = calc.forward("integrate(x**2, (x, 0, 1))")

    assert result == "1/3"

def test_cpu_timeout(): # try to overrun cpu time
    calc = CalculatorTool()

    expr = "factor(expand((x+1)**200 - (x-1)**200))"
    result = calc.forward(expr)

    assert result.startswith("Error:") 

def test_memory_exhaustion(): # try to overrun memory
    calc = CalculatorTool()

    expr = "expand((x + y + z + w)**50)"
    result = calc.forward(expr)

    assert result.startswith("Error:")

def test_malformed_input():
    calc = CalculatorTool()

    result = calc.forward("2 + + + / nonsense((")

    assert result.startswith("Error:")


