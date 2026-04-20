from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from .common import CaseParticipantRole
from .yuanqi import YuanqiWorkflowInvocation


class TrialStage(StrEnum):
    PREPARE = "prepare"
    INVESTIGATION = "investigation"
    EVIDENCE = "evidence"
    DEBATE = "debate"
    FINAL_STATEMENT = "final_statement"
    MEDIATION_OR_JUDGMENT = "mediation_or_judgment"
    REPORT_READY = "report_ready"


class SimulationCgScene(BaseModel):
    background_id: str = Field(
        default="courtroom_entry",
        description="Stable background identifier for the current CG frame.",
    )
    shot_type: str = Field(
        default="medium",
        description="Camera shot type used by the current CG frame.",
    )
    speaker_role: str = Field(
        default="judge",
        description="Speaker role mirrored into the CG frame.",
    )
    speaker_emotion: str = Field(
        default="calm",
        description="Dominant speaker emotion for the current frame.",
    )
    left_character_id: str | None = Field(
        default=None,
        description="Left-side placeholder character or final art asset ID.",
    )
    right_character_id: str | None = Field(
        default=None,
        description="Right-side placeholder character or final art asset ID.",
    )
    emphasis_target: str | None = Field(
        default=None,
        description="Stage object or evidence target that should be emphasized.",
    )
    effect_id: str | None = Field(
        default=None,
        description="Optional overlay effect identifier for the frame.",
    )
    title: str = Field(
        default="",
        description="Short CG frame title shown in the scene header.",
    )
    caption: str = Field(
        default="",
        description="Short CG caption shown under the visual frame.",
    )
    image_url: str | None = Field(
        default=None,
        description="Generated CG image URL when external image rendering succeeds.",
    )
    image_prompt: str | None = Field(
        default=None,
        description="Prompt used to generate the current CG image for debugging and review.",
    )
    image_model: str | None = Field(
        default=None,
        description="Image model identifier that rendered the current CG frame.",
    )


class SimulationActionCard(BaseModel):
    choice_id: str | None = Field(
        default=None,
        description="Stable workflow choice ID used to advance the simulation.",
    )
    action: str = Field(..., min_length=1, description="Stable action label shown to the user.")
    intent: str = Field(
        default="",
        description="Tactical meaning of the action in the current round.",
    )
    risk_tip: str = Field(
        default="",
        description="Primary risk or tradeoff if the user chooses the action.",
    )
    emphasis: str = Field(
        default="steady",
        description="Visual emphasis level for the action card.",
    )


class SimulationUserInputType(StrEnum):
    FACT = "fact"
    EVIDENCE = "evidence"
    CROSS_EXAM = "cross_exam"
    PROCEDURE_REQUEST = "procedure_request"
    ARGUMENT = "argument"
    CLOSING_STATEMENT = "closing_statement"
    SETTLEMENT_POSITION = "settlement_position"


class SimulationUserInputEntry(BaseModel):
    entry_id: str = Field(..., min_length=1, description="Stable input entry ID.")
    stage: TrialStage = Field(..., description="Stage where the user supplied this input.")
    turn_index: int = Field(..., ge=1, description="Turn index when the input was captured.")
    input_type: SimulationUserInputType = Field(..., description="Normalized user input type.")
    label: str = Field(..., min_length=1, description="Display label for the input type.")
    content: str = Field(..., min_length=1, description="Raw user-supplied content.")
    created_at: str = Field(..., min_length=1, description="ISO timestamp when the input was created.")


class SimulationSnapshot(BaseModel):
    simulation_id: str = Field(..., description="Stable ID for one simulation session.")
    case_id: str = Field(..., description="Case ID bound to the current simulation.")
    current_stage: TrialStage = Field(..., description="Current trial stage.")
    turn_index: int = Field(..., ge=1, description="1-based turn index.")
    node_id: str = Field(
        default="N01",
        description="Current workflow node identifier.",
    )
    branch_focus: str = Field(
        default="general",
        description="Current narrative focus derived from the selected action.",
    )
    scene_title: str = Field(..., min_length=1, description="Current scene title.")
    scene_text: str = Field(..., min_length=1, description="Narrative text for the scene.")
    cg_caption: str = Field(
        default="",
        description="Cinematic caption for the current scene.",
    )
    cg_scene: SimulationCgScene = Field(
        default_factory=SimulationCgScene,
        description="Structured CG scene metadata for layered frontend rendering.",
    )
    court_progress: str = Field(
        default="",
        description="Structured courtroom progress block.",
    )
    pressure_shift: str = Field(
        default="",
        description="Structured pressure-shift block.",
    )
    stage_objective: str = Field(
        default="",
        description="Current stage objective explained in user-facing language.",
    )
    current_task: str = Field(
        default="",
        description="The single most important task the user must respond to right now.",
    )
    choice_prompt: str = Field(
        default="",
        description="Structured choice prompt block.",
    )
    hidden_state_summary: dict[str, str] = Field(
        default_factory=dict,
        description="User-facing summarized hidden-state descriptions.",
    )
    speaker_role: CaseParticipantRole = Field(
        ...,
        description="Primary speaker role for the current scene.",
    )
    available_actions: list[str] = Field(
        default_factory=list,
        description="Actions the user can choose from in the current scene.",
    )
    action_cards: list[SimulationActionCard] = Field(
        default_factory=list,
        description="Structured action cards rendered by the single-thread trial UI.",
    )
    suggested_actions: list[str] = Field(
        default_factory=list,
        description="Optional Yuanqi-suggested actions for the current scene.",
    )
    next_stage_hint: str = Field(
        default="",
        description="Optional stage hint returned by the Yuanqi workflow.",
    )
    legal_support: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured legal-support payload merged from Yuanqi.",
    )
    opponent: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured opponent-behavior payload merged from Yuanqi.",
    )
    analysis: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured analysis/report payload merged from Yuanqi.",
    )
    degraded_flags: list[str] = Field(
        default_factory=list,
        description="Execution degradation flags produced by Yuanqi orchestration.",
    )
    user_input_entries: list[SimulationUserInputEntry] = Field(
        default_factory=list,
        description="Structured supplemental user inputs accumulated during the simulation.",
    )
    yuanqi_branch_name: str | None = Field(
        default=None,
        description="Resolved W00 branch name when Yuanqi execution succeeded.",
    )
    workflow_hints: list[YuanqiWorkflowInvocation] = Field(
        default_factory=list,
        description="Prepared Yuanqi workflow payloads for the current scene.",
    )


class SimulationTurnRequest(BaseModel):
    simulation_id: str = Field(..., description="Current simulation session ID.")
    current_stage: TrialStage = Field(..., description="Current stage before advancing.")
    turn_index: int = Field(..., ge=1, description="Current turn index before advancing.")
    selected_action: str = Field(..., min_length=1, description="Action chosen by the user.")
    selected_choice_id: str | None = Field(
        default=None,
        description="Optional structured choice ID matching the current workflow node.",
    )
    user_input_entries: list[SimulationUserInputEntry] = Field(
        default_factory=list,
        description="Full accumulated supplemental user-input entries available before advancing.",
    )
