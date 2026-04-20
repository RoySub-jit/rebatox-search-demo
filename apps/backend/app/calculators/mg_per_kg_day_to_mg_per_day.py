from __future__ import annotations

from app.calculators.common import build_response, is_negative, is_non_positive, ZERO
from app.schemas.calculators import CalculatorResponse, MgPerKgDayToMgPerDayInput

FORMULA = "mg/day = mg/kg/day * body_weight_kg"
ASSUMPTIONS = [
    "The dose and body weight are expressed on the same day-based basis.",
    "The output preserves the source mass unit in milligrams per day.",
]


def calculate_mg_per_kg_day_to_mg_per_day(
    payload: MgPerKgDayToMgPerDayInput,
) -> CalculatorResponse:
    warnings: list[str] = []

    if is_negative(payload.dose_mg_per_kg_day):
        return build_response(
            calculator="mg_per_kg_day_to_mg_per_day",
            formula=FORMULA,
            inputs=payload,
            assumptions=ASSUMPTIONS,
            result=None,
            warnings=["Dose in mg/kg/day must be greater than or equal to 0."],
            status="error",
        )

    if is_non_positive(payload.body_weight_kg):
        return build_response(
            calculator="mg_per_kg_day_to_mg_per_day",
            formula=FORMULA,
            inputs=payload,
            assumptions=ASSUMPTIONS,
            result=None,
            warnings=["Body weight in kg must be greater than 0."],
            status="error",
        )

    result_value = payload.dose_mg_per_kg_day * payload.body_weight_kg

    if payload.dose_mg_per_kg_day == ZERO:
        warnings.append("Dose is 0 mg/kg/day, so the converted daily dose is 0 mg/day.")

    return build_response(
        calculator="mg_per_kg_day_to_mg_per_day",
        formula=FORMULA,
        inputs=payload,
        assumptions=ASSUMPTIONS,
        result={"value": result_value, "unit": "mg/day"},
        warnings=warnings,
    )
