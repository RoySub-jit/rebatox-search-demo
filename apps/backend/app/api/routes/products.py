from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.errors import ErrorResponse
from app.schemas.products import ProductCreate, ProductRead
from app.services.products import create_product, get_product_by_id

router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    },
)
def create_product_route(
    payload: ProductCreate,
    db: Session = Depends(get_db),
) -> ProductRead:
    product = create_product(db=db, payload=payload)
    return ProductRead.model_validate(product)


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    },
)
def get_product_route(
    product_id: int,
    db: Session = Depends(get_db),
) -> ProductRead:
    product = get_product_by_id(db=db, product_id=product_id)
    return ProductRead.model_validate(product)
