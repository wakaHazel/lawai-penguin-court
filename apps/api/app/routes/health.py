from fastapi import APIRouter

from ..schemas.common import ResponseEnvelope

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ResponseEnvelope)
def health_check() -> ResponseEnvelope:
    return ResponseEnvelope(
        success=True,
        message="ok",
        data={"status": "healthy"},
        error_code=None,
    )
