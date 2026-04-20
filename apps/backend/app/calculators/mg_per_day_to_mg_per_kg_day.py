from __future__ import annotations

from app.calculators.common import build_response, is_negative, is_non_positive, ZERO
from app.schemas.calculators import CalculatorResponse, MgPerDayToMgPerKgDayInput

FORMULA = "mg/kg/day = mg/day / body_weight_kg"
ASSUMPTIONS = [
    "The daily dose and body weight refer to the same individual or population weight basis.",
    "The output is normalized to body weight in kilograms.",
]


def calculate_mg_per_day_to_mg_per_kg_day(
    payload: MgPerDayToMgPerKgDayInput,
) -> CalculatorResponse:
    warnings: list[str] = []

    if is_negative(payload.dose_mg_per_day):
        return build_response(
            calculator="mg_per_day_to_mg_per_kg_day",
            formula=FORMULA,
            inputs=payload,
            assumptions=ASSUMPTIONS,
            result=None,
            warnings=["Dose in mg/day must be greater than or equal to 0."],
            status="error",
        )

    if is_non_positive(payload.body_weight_kg):
        return build_response(
            calculator="mg_per_day_to_mg_per_kg_day",
            formula=FORMULA,
            inputs=payload,
            assumptions=ASSUMPTIONS,
            result=None,
            warnings=["Body weight in kg must be greater than 0."],
            status="error",
        )

    result_value = payload.dose_mg_per_day / payload.body_weight_kg

    if payload.dose_mg_per_day == ZERO:
        warnings.append("Dose is 0 mg/day, so the normalized dose is 0 mg/kg/day.")

    return build_response(
        calculator="mg_per_day_to_mg_per_kg_day",
        formula=FORMULA,
        inputs=payload,
        assumptions=ASSUMPTIONS,
        result={"value": result_value, "unit": "mg/kg/day"},
        warnings=warnings,
    )
