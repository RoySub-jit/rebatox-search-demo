from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field

CalculationStatus = Literal["ok", "warning", "error"]


class CalculatorResponse(BaseModel):
    calculator: str
    formula: str
    inputs: dict[str, Any]
    assumptions: list[str] = Field(default_factory=list)
    result: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    status: CalculationStatus


class MgPerKgDayToMgPerDayInput(BaseModel):
    dose_mg_per_kg_day: Decimal
    body_weight_kg: Decimal


class MgPerDayToMgPerKgDayInput(BaseModel):
    dose_mg_per_day: Decimal
    body_weight_kg: Decimal


class MarginOfExposureInput(BaseModel):
    point_of_departure: Decimal
    exposure: Decimal
    basis: str = "mg/kg/day"


class PdeAdeCalculatorInput(BaseModel):
    calculator_type: Literal["pde", "ade"]
    point_of_departure_mg_per_kg_day: Decimal
    body_weight_kg: Decimal = Field(default=Decimal("50"))
    modifying_factor_f1: Decimal = Field(default=Decimal("1"))
    modifying_factor_f2: Decimal = Field(default=Decimal("1"))
    modifying_factor_f3: Decimal = Field(default=Decimal("1"))
    modifying_factor_f4: Decimal = Field(default=Decimal("1"))
    modifying_factor_f5: Decimal = Field(default=Decimal("1"))
    point_of_departure_label: str = "POD"
    result_unit: str = "mg/day"
