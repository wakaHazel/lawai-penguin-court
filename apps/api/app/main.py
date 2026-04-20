from pathlib import Path
from typing import Any
import os

from .env_loader import load_local_env_files

load_local_env_files()

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .database import (
    get_generated_cg_dir,
    get_static_cg_library_dir,
    get_workspace_root,
    initialize_database,
)
from .schemas.common import ResponseEnvelope
from .routes.analysis import router as analysis_router
from .routes.cases import router as cases_router
from .routes.health import router as health_router
from .routes.simulation import router as simulation_router

_ROOT_DIR = get_workspace_root()
_GENERATED_CG_DIR = get_generated_cg_dir()
_STATIC_CG_LIBRARY_DIR = get_static_cg_library_dir()
_WEB_DIST_DIR = _ROOT_DIR / "apps" / "web" / "dist"
_WEB_INDEX_FILE = _WEB_DIST_DIR / "index.html"
_WEB_ASSETS_DIR = _WEB_DIST_DIR / "assets"

app = FastAPI(
    title="Penguin Court API",
    description="Minimal intake-first API skeleton for the D06 courtroom simulation MVP.",
    version="0.1.0",
)

_LOCAL_FRONTEND_ORIGINS = [
    "http://127.0.0.1:4173",
    "http://localhost:4173",
    "http://127.0.0.1:4174",
    "http://localhost:4174",
    "http://127.0.0.1:4175",
    "http://localhost:4175",
]

def _read_allowed_origins() -> list[str]:
    configured = os.getenv("PENGUIN_CORS_ORIGINS", "").strip()
    if not configured:
        return list(_LOCAL_FRONTEND_ORIGINS)

    extras = [
        origin.strip()
        for origin in configured.split(",")
        if origin.strip()
    ]
    return list(dict.fromkeys([*_LOCAL_FRONTEND_ORIGINS, *extras]))


app.add_middleware(
    CORSMiddleware,
    allow_origins=_read_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(cases_router)
app.include_router(simulation_router)
app.include_router(analysis_router)
app.mount(
    "/generated-cg",
    StaticFiles(directory=str(_GENERATED_CG_DIR), check_dir=False),
    name="generated-cg",
)
app.mount(
    "/generated-cg-library",
    StaticFiles(directory=str(_STATIC_CG_LIBRARY_DIR), check_dir=False),
    name="generated-cg-library",
)
app.mount(
    "/assets",
    StaticFiles(directory=str(_WEB_ASSETS_DIR), check_dir=False),
    name="frontend-assets",
)


@app.on_event("startup")
def startup_event() -> None:
    initialize_database()


def _extract_error_payload(detail: Any) -> tuple[str, str | None]:
    if isinstance(detail, dict):
        message = str(detail.get("message") or detail.get("detail") or "request_failed")
        error_code = detail.get("error_code")
        return message, str(error_code) if error_code else message

    if isinstance(detail, str):
        return detail, detail

    return "request_failed", "request_failed"


@app.exception_handler(HTTPException)
async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    message, error_code = _extract_error_payload(exc.detail)
    envelope = ResponseEnvelope(
        success=False,
        message=message,
        data=None,
        error_code=error_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=envelope.model_dump(mode="json"),
    )


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(
    _: Request,
    __: RequestValidationError,
) -> JSONResponse:
    envelope = ResponseEnvelope(
        success=False,
        message="request_validation_failed",
        data=None,
        error_code="request_validation_failed",
    )
    return JSONResponse(
        status_code=422,
        content=envelope.model_dump(mode="json"),
    )


@app.get("/", include_in_schema=False)
async def serve_frontend_root() -> FileResponse:
    if not _WEB_INDEX_FILE.is_file():
        raise HTTPException(status_code=404, detail="frontend_build_missing")
    return FileResponse(_WEB_INDEX_FILE)


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend_app(full_path: str) -> FileResponse:
    reserved_prefixes = (
        "api",
        "health",
        "generated-cg",
        "generated-cg-library",
        "assets",
        "docs",
        "redoc",
        "openapi.json",
    )
    if full_path.startswith(reserved_prefixes):
        raise HTTPException(status_code=404, detail="route_not_found")

    if full_path:
        requested_file = (_WEB_DIST_DIR / full_path).resolve()
        if requested_file.is_file() and _WEB_DIST_DIR in requested_file.parents:
            return FileResponse(requested_file)

    if not _WEB_INDEX_FILE.is_file():
        raise HTTPException(status_code=404, detail="frontend_build_missing")

    return FileResponse(_WEB_INDEX_FILE)
