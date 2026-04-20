from pydantic import BaseModel, Field, model_validator

from .common import (
    CaseDomain,
    CaseParticipantRole,
    CaseType,
    EvidenceStrength,
    EvidenceType,
    UserPerspectiveRole,
    UserGoal,
)

CASE_TYPE_DOMAIN_MAP: dict[CaseType, CaseDomain] = {
    CaseType.PRIVATE_LENDING: CaseDomain.CIVIL,
    CaseType.LABOR_DISPUTE: CaseDomain.CIVIL,
    CaseType.DIVORCE_DISPUTE: CaseDomain.CIVIL,
    CaseType.TORT_LIABILITY: CaseDomain.CIVIL,
}


class PartyProfile(BaseModel):
    party_id: str | None = Field(default=None, description="Optional stable party ID.")
    role: CaseParticipantRole = Field(..., description="Participant role in the case.")
    display_name: str = Field(..., min_length=1, description="Display name for the party.")
    relation_to_case: str | None = Field(
        default=None,
        description="Relationship or identity note, such as borrower or spouse.",
    )
    stance_summary: str | None = Field(
        default=None,
        description="Short summary of the party's current position.",
    )


class EvidenceItem(BaseModel):
    evidence_id: str | None = Field(default=None, description="Optional stable evidence ID.")
    name: str = Field(..., min_length=1, description="Evidence display name.")
    evidence_type: EvidenceType = Field(..., description="Normalized evidence type.")
    summary: str = Field(..., min_length=1, description="What the evidence shows.")
    source: str | None = Field(
        default=None,
        description="Where the evidence comes from, such as user upload or transcript.",
    )
    supports: list[str] = Field(
        default_factory=list,
        description="Focus issues or claims supported by this evidence.",
    )
    risk_points: list[str] = Field(
        default_factory=list,
        description="Known risks, authenticity problems, or proof weaknesses.",
    )
    strength: EvidenceStrength = Field(
        default=EvidenceStrength.UNASSESSED,
        description="Current evidence strength assessment.",
    )
    is_available: bool = Field(
        default=True,
        description="Whether the evidence is currently available to the user.",
    )


class OpponentProfile(BaseModel):
    role: CaseParticipantRole = Field(..., description="Opponent role in the case.")
    display_name: str = Field(..., min_length=1, description="Opponent display name.")
    likely_arguments: list[str] = Field(
        default_factory=list,
        description="Likely arguments or defenses the opponent may raise.",
    )
    likely_evidence: list[str] = Field(
        default_factory=list,
        description="Likely evidence the opponent may submit.",
    )
    likely_strategies: list[str] = Field(
        default_factory=list,
        description="Likely courtroom strategies or behavior patterns.",
    )


class TimelineEvent(BaseModel):
    event_id: str | None = Field(default=None, description="Optional stable timeline event ID.")
    time_label: str = Field(
        ...,
        min_length=1,
        description="Displayable time marker, such as a date or phase label.",
    )
    event_text: str = Field(
        ...,
        min_length=1,
        description="Structured description of a key case event.",
    )
    significance: str | None = Field(
        default=None,
        description="Why the event matters to the dispute or simulation.",
    )
    related_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence items connected to this event.",
    )


class CaseProfile(BaseModel):
    """Frozen MVP case intake structure shared across frontend and backend."""

    case_id: str | None = Field(default=None, description="Optional stable case ID.")
    domain: CaseDomain = Field(..., description="Top-level legal domain.")
    case_type: CaseType = Field(..., description="MVP case subtype.")
    title: str = Field(..., min_length=1, description="Short case title.")
    summary: str = Field(..., min_length=1, description="Case summary in plain language.")
    user_perspective_role: UserPerspectiveRole = Field(
        ...,
        description="Product-side perspective used by the current user during simulation.",
    )
    user_goals: list[UserGoal] = Field(
        default_factory=list,
        description="What the user wants the system to help with.",
    )
    parties: list[PartyProfile] = Field(
        default_factory=list,
        description="All known parties involved in the case.",
    )
    claims: list[str] = Field(
        default_factory=list,
        description="Primary requests or claims raised by the user side.",
    )
    core_facts: list[str] = Field(
        default_factory=list,
        description="Key facts already known and accepted for intake.",
    )
    timeline_events: list[TimelineEvent] = Field(
        default_factory=list,
        description="Structured timeline of key dispute events for later simulation stages.",
    )
    focus_issues: list[str] = Field(
        default_factory=list,
        description="Core disputed issues identified at intake.",
    )
    evidence_items: list[EvidenceItem] = Field(
        default_factory=list,
        description="Evidence currently held by the user side.",
    )
    missing_evidence: list[str] = Field(
        default_factory=list,
        description="Evidence gaps that should be filled later.",
    )
    opponent_profile: OpponentProfile | None = Field(
        default=None,
        description="Optional structured snapshot of the opposing side.",
    )
    notes: str | None = Field(
        default=None,
        description="Free-form intake notes that do not fit the main schema.",
    )

    @model_validator(mode="after")
    def validate_domain_case_type_match(self) -> "CaseProfile":
        expected_domain = CASE_TYPE_DOMAIN_MAP[self.case_type]
        if self.domain != expected_domain:
            raise ValueError(
                f"case_type '{self.case_type}' must belong to domain '{expected_domain}', "
                f"got '{self.domain}'"
            )
        return self
