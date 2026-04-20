from __future__ import annotations

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errors import raise_api_error
from app.models.catalog import Product
from app.schemas.products import ProductCreate


def create_product(*, db: Session, payload: ProductCreate) -> Product:
    product = Product(**payload.model_dump())
    db.add(product)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="product_slug_conflict",
            message=f"Product slug '{payload.slug}' already exists.",
        )

    db.refresh(product)
    return product


def get_product_by_id(*, db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="product_not_found",
            message=f"Product with id {product_id} was not found.",
        )

    return product
