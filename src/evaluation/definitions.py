from core.registry import Registry
from evaluation.base import VerificationResult

import re
import json

verifier_registry = Registry("verifiers")

@verifier_registry.register("content:contains_str")
def contains_str(got: str, expected: str, case_sensitive: bool = False) -> VerificationResult:
    if case_sensitive:
        passed = expected in got
    else:
        passed = expected.lower() in got.lower()
    return VerificationResult(passed = passed, details=f"Got: {got} Expected: {expected}")

@verifier_registry.register("content:exact_str_match")
def exact_str_match(got: str, expected: str, case_sensitive: bool = False) -> VerificationResult:
    if case_sensitive:
        passed = expected.strip() == got.strip()
    else:
        passed = expected.strip().lower() == got.strip().lower()
    return VerificationResult(passed = passed, details=f"Got: {got} Expected: {expected}")

@verifier_registry.register("content:numeric_match")
def single_numeric_match(got: str, expected: str, tol: float = 0.0, index: int = -1) -> VerificationResult:
    matches = re.findall(r"-?\d+\.?\d*", got)
    if not matches:
        return VerificationResult(passed=False, details=f"No numeric types included in answer - Got: {got}")
    try:
        got_val = float(matches[index])
    except IndexError:
        return VerificationResult(passed=False, details=f"Index {index} out of range for expected: {expected} and \
                                  received strings: {got}")
    try:
        expected_val = float(expected)
    except ValueError:
        return VerificationResult(passed=False, details=f"Expected value: {expected} is not a numeric type")

    passed = abs(got_val - expected_val) <= tol
    return VerificationResult(passed = passed, details=f"Expected value: {expected_val} Got value: {got_val} diff \
            {abs(got_val - expected_val)} and tol: {tol}" )

@verifier_registry.register("content:numeric_within_range")
def numeric_within_range(got: str, minimum: float, maximum: float, index: int = -1) -> VerificationResult:
    matches = re.findall(r"-?\d+\.?\d*", got)
    if not matches:
        return VerificationResult(passed=False, details=f"No numeric types included in answer - Got: {got}")
    try:
        got_val = float(matches[index])
    except IndexError:
        return VerificationResult(passed=False, details=f"Index {index} out of range in received string: {got}")

    passed = got_val <= maximum and got_val >= minimum
    return VerificationResult(passed=passed, details=f"Got value: {got_val} minimum: {minimum} and maximum: {maximum}")

@verifier_registry.register("content:paper_json_match")
def paper_list_match(got: str, expected: list[dict], match_mode: str = "all") -> VerificationResult:
    try:
        parsed = json.loads(got)
        papers = parsed.get("papers", [])
    except (json.JSONDecodeError, AttributeError):
        return VerificationResult(passed=False, details="could not parse 'papers' field from output")

    got_ids = {p.get("arxiv_id", "")  for p in papers if isinstance(p, dict)}
    expected_ids = {p["arxiv_id"] for p in expected}

    if not expected_ids:
        passed = len(got_ids) == 0
        return VerificationResult(passed=passed, details=f"expected no papers, got {len(got_ids)}")

    matched = got_ids & expected_ids

    if match_mode == "all":
        passed = expected_ids.issubset(got_ids)
    else:  
        passed = len(matched) > 0

    return VerificationResult(passed=passed, details=f"matched {len(matched)}/{len(expected_ids)} expected papers")

@verifier_registry.register("format:json_output")
def json_output(got: str) -> VerificationResult:
    try:
        payload = json.loads(got)
    except json.JSONDecodeError as e:
        return VerificationResult(passed=False, details=f"Failed to parse as json: {e}")
    return VerificationResult(passed=True, details="Valid Json provided")
