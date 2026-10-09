from fastapi import APIRouter

from .repositories import router as repository_router

api_router = APIRouter()

api_router.include_router(repository_router)
