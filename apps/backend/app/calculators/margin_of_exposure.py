from __future__ import annotations

from app.calculators.common import build_response, is_non_positive
from app.schemas.calculators import CalculatorResponse, MarginOfExposureInput

FORMULA = "margin_of_exposure = point_of_departure / exposure"
ASSUMPTIONS = [
    "Point of departure and exposure are expressed on the same dose and time basis.",
    "Margin of exposure is unitless.",
]


def calculate_margin_of_exposure(
    payload: MarginOfExposureInput,
) -> CalculatorResponse:
    warnings: list[str] = []

    if is_non_positive(payload.point_of_departure):
        return build_response(
            calculator="margin_of_exposure",
            formula=FORMULA,
            inputs=payload,
            assumptions=ASSUMPTIONS,
            result=None,
            warnings=["Point of departure must be greater than 0."],
            status="error",
        )

    if is_non_positive(payload.exposure):
        return build_response(
            calculator="margin_of_exposure",
            formula=FORMULA,
            inputs=payload,
            assumptions=ASSUMPTIONS,
            result=None,
            warnings=["Exposure must be greater than 0 to calculate margin of exposure."],
            status="error",
        )

    result_value = payload.point_of_departure / payload.exposure

    if result_value < 1:
        warnings.append("Exposure exceeds the point of departure, resulting in a margin of exposure below 1.")

    return build_response(
        calculator="margin_of_exposure",
        formula=FORMULA,
        inputs=payload,
        assumptions=ASSUMPTIONS + [f"Basis used for both inputs: {payload.basis}."],
        result={"value": result_value, "unit": "unitless"},
        warnings=warnings,
    )
