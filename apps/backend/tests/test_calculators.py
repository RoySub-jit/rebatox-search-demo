from __future__ import annotations

from decimal import Decimal

from app.calculators.margin_of_exposure import calculate_margin_of_exposure
from app.calculators.mg_per_day_to_mg_per_kg_day import (
    calculate_mg_per_day_to_mg_per_kg_day,
)
from app.calculators.mg_per_kg_day_to_mg_per_day import (
    calculate_mg_per_kg_day_to_mg_per_day,
)
from app.calculators.pde_ade import calculate_pde_ade
from app.schemas.calculators import (
    MarginOfExposureInput,
    MgPerDayToMgPerKgDayInput,
    MgPerKgDayToMgPerDayInput,
    PdeAdeCalculatorInput,
)


def test_mg_per_kg_day_to_mg_per_day_returns_expected_result():
    response = calculate_mg_per_kg_day_to_mg_per_day(
        MgPerKgDayToMgPerDayInput(
            dose_mg_per_kg_day=Decimal("2.5"),
            body_weight_kg=Decimal("70"),
        )
    )

    assert response.status == "ok"
    assert response.formula == "mg/day = mg/kg/day * body_weight_kg"
    assert response.result == {"value": Decimal("175.0"), "unit": "mg/day"}
    assert response.warnings == []


def test_mg_per_day_to_mg_per_kg_day_returns_expected_result():
    response = calculate_mg_per_day_to_mg_per_kg_day(
        MgPerDayToMgPerKgDayInput(
            dose_mg_per_day=Decimal("175"),
            body_weight_kg=Decimal("70"),
        )
    )

    assert response.status == "ok"
    assert response.result == {"value": Decimal("2.5"), "unit": "mg/kg/day"}


def test_mg_per_day_to_mg_per_kg_day_returns_error_for_zero_body_weight():
    response = calculate_mg_per_day_to_mg_per_kg_day(
        MgPerDayToMgPerKgDayInput(
            dose_mg_per_day=Decimal("100"),
            body_weight_kg=Decimal("0"),
        )
    )

    assert response.status == "error"
    assert response.result is None
    assert response.warnings == ["Body weight in kg must be greater than 0."]


def test_margin_of_exposure_returns_expected_result():
    response = calculate_margin_of_exposure(
        MarginOfExposureInput(
            point_of_departure=Decimal("100"),
            exposure=Decimal("2"),
            basis="mg/kg/day",
        )
    )

    assert response.status == "ok"
    assert response.result == {"value": Decimal("50"), "unit": "unitless"}
    assert "Basis used for both inputs: mg/kg/day." in response.assumptions


def test_margin_of_exposure_warns_when_exposure_exceeds_point_of_departure():
    response = calculate_margin_of_exposure(
        MarginOfExposureInput(
            point_of_departure=Decimal("1"),
            exposure=Decimal("2"),
        )
    )

    assert response.status == "warning"
    assert response.result == {"value": Decimal("0.5"), "unit": "unitless"}
    assert response.warnings == [
        "Exposure exceeds the point of departure, resulting in a margin of exposure below 1."
    ]


def test_margin_of_exposure_errors_on_zero_exposure():
    response = calculate_margin_of_exposure(
        MarginOfExposureInput(
            point_of_departure=Decimal("100"),
            exposure=Decimal("0"),
        )
    )

    assert response.status == "error"
    assert response.result is None
    assert response.warnings == [
        "Exposure must be greater than 0 to calculate margin of exposure."
    ]


def test_pde_shell_returns_expected_result():
    response = calculate_pde_ade(
        PdeAdeCalculatorInput(
            calculator_type="pde",
            point_of_departure_mg_per_kg_day=Decimal("5"),
            body_weight_kg=Decimal("50"),
            modifying_factor_f1=Decimal("2"),
            modifying_factor_f2=Decimal("5"),
            modifying_factor_f3=Decimal("10"),
            modifying_factor_f4=Decimal("1"),
            modifying_factor_f5=Decimal("1"),
            point_of_departure_label="NOAEL",
        )
    )

    assert response.status == "ok"
    assert response.calculator == "pde_calculator_shell"
    assert response.result == {
        "value": Decimal("2.5"),
        "unit": "mg/day",
        "composite_modifying_factor": Decimal("100"),
        "point_of_departure_label": "NOAEL",
    }


def test_ade_shell_warns_when_all_modifying_factors_are_unity():
    response = calculate_pde_ade(
        PdeAdeCalculatorInput(
            calculator_type="ade",
            point_of_departure_mg_per_kg_day=Decimal("0.6"),
        )
    )

    assert response.status == "warning"
    assert response.calculator == "ade_calculator_shell"
    assert response.result == {
        "value": Decimal("30.0"),
        "unit": "mg/day",
        "composite_modifying_factor": Decimal("1"),
        "point_of_departure_label": "POD",
    }
    assert response.warnings == [
        "All modifying factors are 1, so no uncertainty adjustment has been applied."
    ]


def test_pde_shell_errors_on_invalid_modifying_factor():
    response = calculate_pde_ade(
        PdeAdeCalculatorInput(
            calculator_type="pde",
            point_of_departure_mg_per_kg_day=Decimal("1"),
            modifying_factor_f3=Decimal("0"),
        )
    )

    assert response.status == "error"
    assert response.result is None
    assert response.warnings == [
        "All modifying factors must be greater than 0. Invalid factors: F3."
    ]
