from pathlib import Path
from typing import Any

from .env_loader import load_local_env_files

load_local_env_files()

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .database import initialize_database
from .schemas.common import ResponseEnvelope
from .routes.analysis import router as analysis_router
from .routes.cases import router as cases_router
from .routes.health import router as health_router
from .routes.simulation import router as simulation_router

_ROOT_DIR = Path(__file__).resolve().parents[3]
_GENERATED_CG_DIR = _ROOT_DIR / "data" / "generated-cg"
_STATIC_CG_LIBRARY_DIR = _ROOT_DIR / "data" / "cg-library"

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=_LOCAL_FRONTEND_ORIGINS,
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
