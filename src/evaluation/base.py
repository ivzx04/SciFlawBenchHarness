from typing import List, Callable, Any

from pydantic import BaseModel, Field


class VerificationResult(BaseModel):
    passed: bool
    details: str

class VerifierDef(BaseModel):
    name: str
    kwargs: dict = Field(default_factory=dict)

def run_check(f: Callable, got: str, **kwargs) -> VerificationResult:
    try:
        return f(got, **kwargs)
    except Exception as e:
        return VerificationResult(passed=False, details=f"Failed to run verifier with following exception: {e}")
