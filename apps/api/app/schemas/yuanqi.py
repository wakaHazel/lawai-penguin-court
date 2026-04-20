from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class YuanqiWorkflowKey(StrEnum):
    MASTER_ORCHESTRATION = "master_orchestration"
    COURTROOM_SCENE_GENERATION = "courtroom_scene_generation"
    LEGAL_SUPPORT_RETRIEVAL = "legal_support_retrieval"
    OPPONENT_BEHAVIOR_SIMULATION = "opponent_behavior_simulation"
    OUTCOME_ANALYSIS_REPORT = "outcome_analysis_report"


class YuanqiWorkflowInvocation(BaseModel):
    workflow_key: YuanqiWorkflowKey = Field(
        ...,
        description="Stable internal workflow key mapped to a Yuanqi workflow.",
    )
    workflow_version: str = Field(
        default="2026-04-15-export",
        description="Version tag aligned to the audited Yuanqi export package.",
    )
    variables: dict[str, str] = Field(
        default_factory=dict,
        description="Null-safe variables prepared for Yuanqi workflow execution.",
    )


class YuanqiMessageContentItem(BaseModel):
    type: str = Field(default="text", description="Published API content item type.")
    text: str = Field(..., description="Text content sent to the published assistant.")


class YuanqiChatMessage(BaseModel):
    role: str = Field(default="user", description="Chat role for the published API.")
    content: list[YuanqiMessageContentItem] = Field(
        default_factory=list,
        description="Message content items in the official Yuanqi format.",
    )


class YuanqiChatCompletionRequest(BaseModel):
    assistant_id: str = Field(..., description="Published Yuanqi assistant ID.")
    user_id: str = Field(..., description="Stable caller identity for the session.")
    messages: list[YuanqiChatMessage] = Field(
        default_factory=list,
        description="Chat messages passed to the Yuanqi published API.",
    )
    stream: bool = Field(
        default=False,
        description="The backend uses non-streaming mode for deterministic parsing.",
    )
    custom_variables: dict[str, Any] = Field(
        default_factory=dict,
        description="Official Yuanqi workflow variables passed through custom_variables.",
    )


class YuanqiAssistantMessage(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: str = Field(default="assistant")
    content: Any = Field(default="")


class YuanqiChoice(BaseModel):
    model_config = ConfigDict(extra="allow")

    message: YuanqiAssistantMessage = Field(default_factory=YuanqiAssistantMessage)


class YuanqiChatCompletionOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    branch_name: str | None = None
    final_out: Any | None = None
    result_json: Any | None = None


class YuanqiChatCompletionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    choices: list[YuanqiChoice] = Field(default_factory=list)
    output: YuanqiChatCompletionOutput | None = None


class YuanqiMergedResult(BaseModel):
    status: str = Field(default="ok")
    stage: str = Field(default="")
    scene: dict[str, Any] = Field(default_factory=dict)
    legal_support: dict[str, Any] = Field(default_factory=dict)
    opponent: dict[str, Any] = Field(default_factory=dict)
    analysis: dict[str, Any] = Field(default_factory=dict)
    degraded_flags: list[str] = Field(default_factory=list)
    branch_name: str | None = Field(default=None)
