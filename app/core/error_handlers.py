from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging_config import logging


async def custom_starlette_http_exception_handler(
    request: Request, exc: StarletteHTTPException
):
    logging.error(exc.detail)
    return JSONResponse(
        status_code=exc.status_code, content={"success": False, "message": exc.detail}
    )


async def custom_http_exception_handler(request: Request, exc: HTTPException):
    logging.error(exc.detail)
    return JSONResponse(
        status_code=exc.status_code, content={"success": False, "message": exc.detail}
    )


async def custom_exception_handler(request: Request, exc: Exception):
    logging.error(exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An unexpected error occurred.",
            "error": str(exc),
        },
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logging.error(exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "A database error occurred.",
            "error": str(exc),
        },
    )
