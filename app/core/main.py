import asyncio
import logging
import sys
import time
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.attendance import routes as attendance_routes
from app.api.auth import routes as auth_routes
from app.api.facilities import routes as facilities_routes
from app.api.files import routes as files_routes
from app.api.inventory import routes as inventory_routes
from app.core.config import settings
from app.core.error_handlers import (
    custom_exception_handler,
    custom_http_exception_handler,
    # custom_request_validation_exception_handler,
    custom_starlette_http_exception_handler,
    # validation_exception_handler
    sqlalchemy_exception_handler,
)
from app.core.middlewares import CustomHeaderMiddleware, TimeoutMiddleware
from app.core.models import *  # noqa: F401, F403

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")


logger = logging.getLogger("tse")
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[logging.FileHandler("errors.log"), logging.StreamHandler()],
)


def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = global_exception_handler


def async_exception_handler(loop, context):
    msg = context.get("exception", context["message"])
    logger.error("Uncaught async exception: %s", msg, exc_info=context.get("exception"))


asyncio.get_event_loop().set_exception_handler(async_exception_handler)


app = FastAPI(
    title=settings.PROJECT_NAME,
    root_path=settings.ROOT_PATH,
)


# app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses larger than 1000 bytes
app.add_middleware(CustomHeaderMiddleware)
app.add_middleware(TimeoutMiddleware, timeout=999)


# app.add_middleware(HTTPSRedirectMiddleware)
# app.add_middleware(ProxyHeadersMiddleware)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://test-apetrol.site",
        "http://localhost:5173",
        "https://test-apetrol.site",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


app.add_exception_handler(HTTPException, custom_http_exception_handler)  # type: ignore
app.add_exception_handler(500, custom_exception_handler)  # type: ignore
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)  # type: ignore
app.add_exception_handler(
    StarletteHTTPException,
    custom_starlette_http_exception_handler,  # type: ignore
)
app.include_router(auth_routes.router)
app.include_router(inventory_routes.router)
app.include_router(files_routes.router)
app.include_router(facilities_routes.router)
app.include_router(attendance_routes.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
