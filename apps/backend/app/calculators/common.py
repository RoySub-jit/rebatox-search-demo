from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from app.schemas.calculators import CalculatorResponse, CalculationStatus

ONE = Decimal("1")
ZERO = Decimal("0")


def build_response(
    *,
    calculator: str,
    formula: str,
    inputs: BaseModel,
    assumptions: list[str],
    result: dict[str, Any] | None,
    warnings: list[str] | None = None,
    status: CalculationStatus | None = None,
) -> CalculatorResponse:
    warnings = warnings or []

    if status is None:
        status = "warning" if warnings else "ok"

    return CalculatorResponse(
        calculator=calculator,
        formula=formula,
        inputs=inputs.model_dump(mode="python"),
        assumptions=assumptions,
        result=result,
        warnings=warnings,
        status=status,
    )


def is_negative(value: Decimal) -> bool:
    return value < ZERO


def is_non_positive(value: Decimal) -> bool:
    return value <= ZERO
