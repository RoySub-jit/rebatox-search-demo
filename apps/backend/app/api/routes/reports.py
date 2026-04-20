from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.errors import ErrorResponse
from app.schemas.reports import ProductReportRead
from app.services.reports import generate_product_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get(
    "/{product_id}",
    response_model=ProductReportRead,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    },
)
def get_product_report_route(
    product_id: int,
    db: Session = Depends(get_db),
) -> ProductReportRead:
    return generate_product_report(db=db, product_id=product_id)
