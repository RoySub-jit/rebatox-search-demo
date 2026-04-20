from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.errors import raise_api_error
from app.calculators import (
    calculate_margin_of_exposure,
    calculate_mg_per_day_to_mg_per_kg_day,
    calculate_mg_per_kg_day_to_mg_per_day,
    calculate_pde_ade,
)
from app.models.catalog import Comparator, Product
from app.models.research import CalculationRun, CandidatePOD, Study
from app.schemas.calculation_runs import CalculationRunRequest, PdeAdeRunInput
from app.schemas.calculators import CalculatorResponse, PdeAdeCalculatorInput


CalculatorFunction = Callable[[BaseModel], CalculatorResponse]
InputAdapter = Callable[[BaseModel, str], BaseModel]


@dataclass(frozen=True)
class CalculatorRegistryEntry:
    execute: CalculatorFunction
    adapt_input: InputAdapter | None = None


def _adapt_pde_ade_input(inputs: BaseModel, run_type: str) -> PdeAdeCalculatorInput:
    if not isinstance(inputs, PdeAdeRunInput):
        raise TypeError("PDE/ADE calculations require PdeAdeRunInput inputs.")

    return PdeAdeCalculatorInput(
        calculator_type=run_type,
        **inputs.model_dump(),
    )


CALCULATOR_REGISTRY: dict[str, CalculatorRegistryEntry] = {
    "mg_per_kg_day_to_mg_per_day": CalculatorRegistryEntry(
        execute=calculate_mg_per_kg_day_to_mg_per_day
    ),
    "mg_per_day_to_mg_per_kg_day": CalculatorRegistryEntry(
        execute=calculate_mg_per_day_to_mg_per_kg_day
    ),
    "margin_of_exposure": CalculatorRegistryEntry(
        execute=calculate_margin_of_exposure
    ),
    "pde": CalculatorRegistryEntry(
        execute=calculate_pde_ade,
        adapt_input=_adapt_pde_ade_input,
    ),
    "ade": CalculatorRegistryEntry(
        execute=calculate_pde_ade,
        adapt_input=_adapt_pde_ade_input,
    ),
}

LINKED_RESOURCE_MAP: tuple[tuple[str, type[Any], str, str], ...] = (
    ("product_id", Product, "product_not_found", "Product"),
    ("comparator_id", Comparator, "comparator_not_found", "Comparator"),
    ("study_id", Study, "study_not_found", "Study"),
    ("candidate_pod_id", CandidatePOD, "candidate_pod_not_found", "Candidate POD"),
)


def _validate_linked_resources(*, db: Session, payload: CalculationRunRequest) -> None:
    for field_name, model, error_code, label in LINKED_RESOURCE_MAP:
        resource_id = getattr(payload, field_name)
        if resource_id is None:
            continue

        if db.get(model, resource_id) is None:
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code=error_code,
                message=f"{label} with id {resource_id} was not found.",
            )


def _run_registered_calculation(payload: CalculationRunRequest) -> CalculatorResponse:
    registry_entry = CALCULATOR_REGISTRY[payload.run_type]
    calculator_input: BaseModel = payload.inputs

    if registry_entry.adapt_input is not None:
        calculator_input = registry_entry.adapt_input(payload.inputs, payload.run_type)

    return registry_entry.execute(calculator_input)


def _error_message_from_calculator(output: CalculatorResponse) -> str:
    if output.warnings:
        return output.warnings[0]

    return "Calculation inputs are invalid."


def run_calculation(*, db: Session, payload: CalculationRunRequest) -> CalculationRun:
    _validate_linked_resources(db=db, payload=payload)

    output = _run_registered_calculation(payload)
    if output.status == "error":
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="calculation_invalid",
            message=_error_message_from_calculator(output),
        )

    now = datetime.now(timezone.utc)
    calculation_run = CalculationRun(
        run_type=payload.run_type,
        status=output.status,
        product_id=payload.product_id,
        comparator_id=payload.comparator_id,
        study_id=payload.study_id,
        candidate_pod_id=payload.candidate_pod_id,
        parameters_json=payload.inputs.model_dump(mode="json"),
        result_json=output.model_dump(mode="json"),
        started_at=now,
        completed_at=now,
    )
    db.add(calculation_run)
    db.commit()
    db.refresh(calculation_run)

    return calculation_run


def get_calculation_run_by_id(*, db: Session, calculation_id: int) -> CalculationRun:
    calculation_run = db.get(CalculationRun, calculation_id)
    if calculation_run is None:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="calculation_run_not_found",
            message=f"Calculation run with id {calculation_id} was not found.",
        )

    return calculation_run
