from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from app.models.research import CalculationRun
from app.schemas.calculators import (
    CalculatorResponse,
    MarginOfExposureInput,
    MgPerDayToMgPerKgDayInput,
    MgPerKgDayToMgPerDayInput,
)


class CalculationLinkFields(BaseModel):
    product_id: int | None = None
    comparator_id: int | None = None
    study_id: int | None = None
    candidate_pod_id: int | None = None


class PdeAdeRunInput(BaseModel):
    point_of_departure_mg_per_kg_day: Decimal
    body_weight_kg: Decimal = Field(default=Decimal("50"))
    modifying_factor_f1: Decimal = Field(default=Decimal("1"))
    modifying_factor_f2: Decimal = Field(default=Decimal("1"))
    modifying_factor_f3: Decimal = Field(default=Decimal("1"))
    modifying_factor_f4: Decimal = Field(default=Decimal("1"))
    modifying_factor_f5: Decimal = Field(default=Decimal("1"))
    point_of_departure_label: str = "POD"
    result_unit: str = "mg/day"


class MgPerKgDayToMgPerDayRunRequest(CalculationLinkFields):
    run_type: Literal["mg_per_kg_day_to_mg_per_day"]
    inputs: MgPerKgDayToMgPerDayInput


class MgPerDayToMgPerKgDayRunRequest(CalculationLinkFields):
    run_type: Literal["mg_per_day_to_mg_per_kg_day"]
    inputs: MgPerDayToMgPerKgDayInput


class MarginOfExposureRunRequest(CalculationLinkFields):
    run_type: Literal["margin_of_exposure"]
    inputs: MarginOfExposureInput


class PdeRunRequest(CalculationLinkFields):
    run_type: Literal["pde"]
    inputs: PdeAdeRunInput


class AdeRunRequest(CalculationLinkFields):
    run_type: Literal["ade"]
    inputs: PdeAdeRunInput


CalculationRunRequest = Annotated[
    MgPerKgDayToMgPerDayRunRequest
    | MgPerDayToMgPerKgDayRunRequest
    | MarginOfExposureRunRequest
    | PdeRunRequest
    | AdeRunRequest,
    Field(discriminator="run_type"),
]


class CalculationRunRead(BaseModel):
    id: int
    run_type: str
    status: str
    product_id: int | None = None
    comparator_id: int | None = None
    study_id: int | None = None
    candidate_pod_id: int | None = None
    inputs: dict[str, Any]
    output: CalculatorResponse
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, calculation_run: CalculationRun) -> "CalculationRunRead":
        return cls(
            id=calculation_run.id,
            run_type=calculation_run.run_type,
            status=calculation_run.status,
            product_id=calculation_run.product_id,
            comparator_id=calculation_run.comparator_id,
            study_id=calculation_run.study_id,
            candidate_pod_id=calculation_run.candidate_pod_id,
            inputs=calculation_run.parameters_json or {},
            output=CalculatorResponse.model_validate(calculation_run.result_json or {}),
            started_at=calculation_run.started_at,
            completed_at=calculation_run.completed_at,
            created_at=calculation_run.created_at,
            updated_at=calculation_run.updated_at,
        )
