import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from ..core.exceptions import CodeAtlasError, GitCloneError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register application-wide exception handlers."""

    @app.exception_handler(GitCloneError)
    async def git_clone_error_handler(
        request: Request,
        exc: GitCloneError,
    ) -> JSONResponse:
        logger.warning(
            "Git clone failed: method=%s path=%s",
            request.method,
            request.url.path,
        )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Failed to clone repository.",
                "code": "GIT_CLONE_ERROR",
            },
        )

    @app.exception_handler(CodeAtlasError)
    async def code_atlas_error_handler(
        request: Request,
        exc: CodeAtlasError,
    ) -> JSONResponse:
        logger.warning(
            "Application error: method=%s path=%s error=%s",
            request.method,
            request.url.path,
            type(exc).__name__,
        )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": str(exc),
                "code": "CODE_ATLAS_ERROR",
            },
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception(
            "Unhandled exception: method=%s path=%s",
            request.method,
            request.url.path,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An unexpected internal server error occurred.",
                "code": "INTERNAL_SERVER_ERROR",
            },
        )
