from fastapi import APIRouter

from .dependency_graph import router as dependency_graph_router
from .repositories import router as repository_router

api_router = APIRouter()

api_router.include_router(repository_router)
api_router.include_router(dependency_graph_router)
