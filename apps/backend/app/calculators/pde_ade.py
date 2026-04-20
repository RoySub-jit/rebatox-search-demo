from __future__ import annotations

from decimal import Decimal

from app.calculators.common import ONE, build_response, is_non_positive
from app.schemas.calculators import CalculatorResponse, PdeAdeCalculatorInput

FORMULA = (
    "result_mg_per_day = point_of_departure_mg_per_kg_day * body_weight_kg / "
    "(F1 * F2 * F3 * F4 * F5)"
)


def calculate_pde_ade(payload: PdeAdeCalculatorInput) -> CalculatorResponse:
    warnings: list[str] = []
    factors = {
        "F1": payload.modifying_factor_f1,
        "F2": payload.modifying_factor_f2,
        "F3": payload.modifying_factor_f3,
        "F4": payload.modifying_factor_f4,
        "F5": payload.modifying_factor_f5,
    }

    if is_non_positive(payload.point_of_departure_mg_per_kg_day):
        return build_response(
            calculator=f"{payload.calculator_type}_calculator_shell",
            formula=FORMULA,
            inputs=payload,
            assumptions=[],
            result=None,
            warnings=["Point of departure in mg/kg/day must be greater than 0."],
            status="error",
        )

    if is_non_positive(payload.body_weight_kg):
        return build_response(
            calculator=f"{payload.calculator_type}_calculator_shell",
            formula=FORMULA,
            inputs=payload,
            assumptions=[],
            result=None,
            warnings=["Body weight in kg must be greater than 0."],
            status="error",
        )

    invalid_factors = [name for name, value in factors.items() if is_non_positive(value)]
    if invalid_factors:
        return build_response(
            calculator=f"{payload.calculator_type}_calculator_shell",
            formula=FORMULA,
            inputs=payload,
            assumptions=[],
            result=None,
            warnings=[f"All modifying factors must be greater than 0. Invalid factors: {', '.join(invalid_factors)}."],
            status="error",
        )

    unusual_factors = [name for name, value in factors.items() if value < ONE]
    if unusual_factors:
        warnings.append(
            f"One or more modifying factors are below 1 ({', '.join(unusual_factors)}); confirm this is intended."
        )

    composite_modifying_factor = Decimal("1")
    for factor in factors.values():
        composite_modifying_factor *= factor

    if composite_modifying_factor == ONE:
        warnings.append("All modifying factors are 1, so no uncertainty adjustment has been applied.")

    result_value = (
        payload.point_of_departure_mg_per_kg_day * payload.body_weight_kg
    ) / composite_modifying_factor

    assumptions = [
        "This shell uses caller-supplied modifying factors and does not infer toxicological defaults.",
        "The point of departure is assumed to be expressed as mg/kg/day.",
        f"The output is expressed as {payload.result_unit}.",
    ]

    if payload.body_weight_kg == Decimal("50"):
        assumptions.append("A 50 kg body weight is commonly used as a regulatory default and is used here when provided.")
    else:
        assumptions.append("A caller-supplied body weight is used instead of a default 50 kg body weight.")

    return build_response(
        calculator=f"{payload.calculator_type}_calculator_shell",
        formula=FORMULA,
        inputs=payload,
        assumptions=assumptions,
        result={
            "value": result_value,
            "unit": payload.result_unit,
            "composite_modifying_factor": composite_modifying_factor,
            "point_of_departure_label": payload.point_of_departure_label,
        },
        warnings=warnings,
    )
