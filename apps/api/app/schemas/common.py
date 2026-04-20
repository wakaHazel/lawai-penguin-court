from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class CaseDomain(StrEnum):
    CIVIL = "civil"
    CRIMINAL = "criminal"
    ADMINISTRATIVE = "administrative"


class CaseType(StrEnum):
    PRIVATE_LENDING = "private_lending"
    LABOR_DISPUTE = "labor_dispute"
    DIVORCE_DISPUTE = "divorce_dispute"
    TORT_LIABILITY = "tort_liability"


class CaseParticipantRole(StrEnum):
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    APPLICANT = "applicant"
    RESPONDENT = "respondent"
    AGENT = "agent"
    WITNESS = "witness"
    JUDGE = "judge"
    OTHER = "other"


class UserPerspectiveRole(StrEnum):
    CLAIMANT_SIDE = "claimant_side"
    RESPONDENT_SIDE = "respondent_side"
    NEUTRAL_OBSERVER = "neutral_observer"
    LEARNER = "learner"
    OTHER = "other"


class UserGoal(StrEnum):
    SIMULATE_TRIAL = "simulate_trial"
    ANALYZE_WIN_RATE = "analyze_win_rate"
    PREPARE_CHECKLIST = "prepare_checklist"
    REVIEW_EVIDENCE = "review_evidence"


class EvidenceType(StrEnum):
    CONTRACT = "contract"
    TRANSFER_RECORD = "transfer_record"
    CHAT_RECORD = "chat_record"
    DOCUMENT = "document"
    AUDIO_VIDEO = "audio_video"
    MEDICAL_RECORD = "medical_record"
    WITNESS_STATEMENT = "witness_statement"
    OTHER = "other"


class EvidenceStrength(StrEnum):
    STRONG = "strong"
    MEDIUM = "medium"
    WEAK = "weak"
    UNASSESSED = "unassessed"


class ResponseEnvelope(BaseModel):
    """Shared response envelope for future case/simulation/report endpoints."""

    success: bool = Field(..., description="Whether the request succeeded.")
    message: str = Field(default="", description="Human-readable status message.")
    data: Any | None = Field(default=None, description="Payload data.")
    error_code: str | None = Field(
        default=None,
        description="Stable machine-readable error code when success is false.",
    )
