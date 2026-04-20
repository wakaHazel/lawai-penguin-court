from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from ..repositories.case_repository import get_case, list_cases, save_case
from ..schemas.case import CaseProfile
from ..schemas.common import ResponseEnvelope

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.post("", response_model=ResponseEnvelope, status_code=status.HTTP_201_CREATED)
def create_case(case_profile: CaseProfile) -> ResponseEnvelope:
    normalized_case = case_profile.model_copy(
        update={"case_id": case_profile.case_id or f"case_{uuid4().hex[:12]}"}
    )
    saved_case = save_case(normalized_case)
    return ResponseEnvelope(
        success=True,
        message="case_intake_created",
        data=saved_case.model_dump(mode="json"),
        error_code=None,
    )


@router.get("", response_model=ResponseEnvelope)
def get_case_list() -> ResponseEnvelope:
    case_profiles = list_cases()
    return ResponseEnvelope(
        success=True,
        message="case_list_loaded",
        data=[case_profile.model_dump(mode="json") for case_profile in case_profiles],
        error_code=None,
    )


@router.get("/{case_id}", response_model=ResponseEnvelope)
def get_case_detail(case_id: str) -> ResponseEnvelope:
    case_profile = get_case(case_id)
    if case_profile is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "case_not_found",
                "error_code": "case_not_found",
            },
        )

    return ResponseEnvelope(
        success=True,
        message="case_detail_loaded",
        data=case_profile.model_dump(mode="json"),
        error_code=None,
    )
