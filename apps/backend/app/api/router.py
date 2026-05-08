from fastapi import APIRouter

from app.api.routes.calculations import router as calculations_router
from app.api.routes.expert_reviews import router as expert_reviews_router
from app.api.routes.health import router as health_router
from app.api.routes.molecule_search import router as molecule_search_router
from app.api.routes.products import router as products_router
from app.api.routes.reports import router as reports_router

api_router = APIRouter()
api_router.include_router(products_router)
api_router.include_router(calculations_router)
api_router.include_router(expert_reviews_router)
api_router.include_router(reports_router)
api_router.include_router(molecule_search_router)
api_router.include_router(health_router)
