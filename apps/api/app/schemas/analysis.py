from datetime import datetime, timezone

from pydantic import BaseModel, Field

from .turn import TrialStage


class SimulationContextRequest(BaseModel):
    simulation_id: str = Field(..., min_length=1, description="Simulation session ID.")


class OpponentBehaviorSnapshot(BaseModel):
    case_id: str = Field(..., description="Case ID.")
    simulation_id: str = Field(..., description="Simulation ID.")
    current_stage: TrialStage = Field(..., description="Current trial stage.")
    opponent_name: str = Field(..., description="Opponent display name.")
    opponent_role: str = Field(..., description="Opponent role.")
    branch_focus: str = Field(..., description="Narrative branch focus.")
    likely_arguments: list[str] = Field(
        default_factory=list,
        description="Likely arguments from the opponent side.",
    )
    likely_evidence: list[str] = Field(
        default_factory=list,
        description="Likely evidence from the opponent side.",
    )
    likely_strategies: list[str] = Field(
        default_factory=list,
        description="Likely opponent strategies.",
    )
    recommended_responses: list[str] = Field(
        default_factory=list,
        description="Suggested responses for current user side.",
    )
    risk_points: list[str] = Field(
        default_factory=list,
        description="Current risk points for hearing strategy.",
    )
    confidence: float = Field(..., ge=0, le=1, description="Confidence score.")


class WinRateAnalysisSnapshot(BaseModel):
    case_id: str = Field(..., description="Case ID.")
    simulation_id: str = Field(..., description="Simulation ID.")
    current_stage: TrialStage = Field(..., description="Current trial stage.")
    estimated_win_rate: int = Field(..., ge=0, le=100, description="Win-rate estimate.")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score.")
    positive_factors: list[str] = Field(
        default_factory=list,
        description="Positive factors for current estimated outcome.",
    )
    negative_factors: list[str] = Field(
        default_factory=list,
        description="Negative factors for current estimated outcome.",
    )
    evidence_gap_actions: list[str] = Field(
        default_factory=list,
        description="Actions to close evidence gaps.",
    )
    recommended_next_actions: list[str] = Field(
        default_factory=list,
        description="Recommended next actions from current stage.",
    )


class ReplayReportSection(BaseModel):
    key: str = Field(..., min_length=1, description="Stable section key.")
    title: str = Field(..., min_length=1, description="Section title.")
    items: list[str] = Field(
        default_factory=list,
        description="Section content lines in display order.",
    )


class ReplayReportSnapshot(BaseModel):
    case_id: str = Field(..., description="Case ID.")
    simulation_id: str = Field(..., description="Simulation ID.")
    report_title: str = Field(..., description="Report title.")
    generated_at: str = Field(..., description="UTC ISO timestamp.")
    current_stage: TrialStage = Field(..., description="Current trial stage.")
    stage_path: list[str] = Field(
        default_factory=list,
        description="Stage path from start to current stage.",
    )
    branch_decisions: list[str] = Field(
        default_factory=list,
        description="Key branch decisions made during this run.",
    )
    state_summary: dict[str, str] = Field(
        default_factory=dict,
        description="Summarized hidden-state explanation for the ending state.",
    )
    report_sections: list[ReplayReportSection] = Field(
        default_factory=list,
        description="Eight fixed report sections for replay and review.",
    )
    report_markdown: str = Field(..., description="Export-friendly markdown report.")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
