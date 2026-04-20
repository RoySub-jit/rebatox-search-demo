from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.calculation_runs import CalculationRunRead, CalculationRunRequest
from app.schemas.errors import ErrorResponse
from app.services.calculations import get_calculation_run_by_id, run_calculation

router = APIRouter(prefix="/calculations", tags=["calculations"])


@router.post(
    "/run",
    response_model=CalculationRunRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    },
)
def run_calculation_route(
    payload: CalculationRunRequest,
    db: Session = Depends(get_db),
) -> CalculationRunRead:
    calculation_run = run_calculation(db=db, payload=payload)
    return CalculationRunRead.from_model(calculation_run)


@router.get(
    "/{calculation_id}",
    response_model=CalculationRunRead,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    },
)
def get_calculation_route(
    calculation_id: int,
    db: Session = Depends(get_db),
) -> CalculationRunRead:
    calculation_run = get_calculation_run_by_id(
        db=db,
        calculation_id=calculation_id,
    )
    return CalculationRunRead.from_model(calculation_run)
