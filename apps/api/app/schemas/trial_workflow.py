from __future__ import annotations

from pydantic import BaseModel, Field

from .common import CaseParticipantRole
from .turn import TrialStage


class HiddenStateSnapshot(BaseModel):
    evidence_strength: int = 50
    procedure_control: int = 50
    judge_trust: int = 50
    opponent_pressure: int = 50
    contradiction_risk: int = 35
    surprise_exposure: int = 20
    settlement_tendency: int = 40


class WorkflowChoice(BaseModel):
    choice_id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    effect_key: str = Field(..., min_length=1)
    next_node_id: str = Field(..., min_length=1)
    intent: str = Field(default="", description="Tactical meaning of this litigation move.")
    risk_tip: str = Field(default="", description="Primary risk if this move is chosen.")
    emphasis: str = Field(default="steady", description="Visual emphasis level for UI rendering.")


class WorkflowNodeDefinition(BaseModel):
    node_id: str = Field(..., min_length=1)
    stage: TrialStage
    title: str = Field(..., min_length=1)
    focus_key: str = Field(..., min_length=1)
    speaker_role: CaseParticipantRole
    stage_objective: str = Field(
        default="",
        description="What this stage is trying to achieve in procedure terms.",
    )
    current_task: str = Field(
        default="",
        description="What the user must respond to in this specific node.",
    )
    checkpoint_enabled: bool = False
    choices: list[WorkflowChoice] = Field(default_factory=list)


class WorkflowEvent(BaseModel):
    event_id: str = Field(..., min_length=1)
    event_type: str = Field(..., min_length=1)
    case_type: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    speaker_role: str = Field(..., min_length=1)
    focus_tags: list[str] = Field(default_factory=list)
    payload: dict[str, str] = Field(default_factory=dict)


class TrialWorkflowDefinition(BaseModel):
    workflow_id: str = Field(..., min_length=1)
    checkpoint_node_ids: list[str] = Field(default_factory=list)
    nodes: list[WorkflowNodeDefinition] = Field(default_factory=list)
    event_pool_keys: list[str] = Field(default_factory=list)


class TrialRunSnapshot(BaseModel):
    trial_run_id: str = Field(..., min_length=1)
    case_id: str = Field(..., min_length=1)
    current_node_id: str = Field(..., min_length=1)
    current_stage: TrialStage
    turn_index: int = Field(..., ge=1)
    state: HiddenStateSnapshot
    visited_node_ids: list[str] = Field(default_factory=list)
    selected_choice_ids: list[str] = Field(default_factory=list)


class RunCheckpointSnapshot(BaseModel):
    checkpoint_id: str = Field(..., min_length=1)
    case_id: str = Field(..., min_length=1)
    trial_run_id: str = Field(..., min_length=1)
    source_node_id: str = Field(..., min_length=1)
    turn_index: int = Field(..., ge=1)
    payload_json: str = Field(..., min_length=1)
