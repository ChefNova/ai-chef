"""Guardrail regression corpus, with independently specified expected results."""
import pytest

from validation.recommendations.cases import CASES
from validation.recommendations.evaluate import check_case


@pytest.mark.parametrize("case", [pytest.param(case, id=case["name"], marks=(
    pytest.mark.xfail(strict=True, reason="Documented ranking limitation")
    if case.get("known_gap") else ())) for case in CASES])
def test_recommendation_accuracy_case(case):
    result = check_case(case)
    assert result["passed"], result
