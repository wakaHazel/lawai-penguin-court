from __future__ import annotations

import json

from ..schemas.case import CaseProfile
from ..schemas.turn import TrialStage
from ..schemas.yuanqi import YuanqiWorkflowInvocation, YuanqiWorkflowKey


class YuanqiBridge:
    """Builds audited per-workflow debug hints aligned to the real export contract."""

    def build_scene_generation_invocation(
        self,
        case_profile: CaseProfile,
        current_stage: TrialStage,
        turn_index: int,
        historical_dialogs: str,
    ) -> YuanqiWorkflowInvocation:
        return YuanqiWorkflowInvocation(
            workflow_key=YuanqiWorkflowKey.COURTROOM_SCENE_GENERATION,
            variables={
                "current_stage": current_stage.value,
                "v_case_summary": case_profile.summary,
                "round_number": str(turn_index),
                "v_historical_dialogs": historical_dialogs,
            },
        )

    def build_legal_retrieval_invocation(
        self,
        case_profile: CaseProfile,
    ) -> YuanqiWorkflowInvocation:
        return YuanqiWorkflowInvocation(
            workflow_key=YuanqiWorkflowKey.LEGAL_SUPPORT_RETRIEVAL,
            variables={
                "case_id": case_profile.case_id or "",
                "case_type": case_profile.case_type.value,
                "focus_issues_json": to_json_string(case_profile.focus_issues),
                "fact_keywords_json": to_json_string(
                    dedupe_text_items(case_profile.core_facts + case_profile.claims)
                ),
            },
        )

    def build_opponent_behavior_invocation(
        self,
        case_profile: CaseProfile,
        current_stage: TrialStage,
        selected_action: str,
    ) -> YuanqiWorkflowInvocation:
        opponent_profile = case_profile.opponent_profile

        return YuanqiWorkflowInvocation(
            workflow_key=YuanqiWorkflowKey.OPPONENT_BEHAVIOR_SIMULATION,
            variables={
                "v_opponent_role": (
                    opponent_profile.role.value if opponent_profile else "other"
                ),
                "v_current_stage": current_stage.value,
                "v_selected_action": selected_action,
                "v_likely_arguments": to_json_string(
                    opponent_profile.likely_arguments if opponent_profile else []
                ),
                "v_focus_issues": to_json_string(case_profile.focus_issues),
            },
        )

    def build_outcome_analysis_invocation(
        self,
        case_profile: CaseProfile,
        legal_support_summary: str,
        simulation_timeline: str,
        opponent_behavior: dict[str, str | list[str]],
    ) -> YuanqiWorkflowInvocation:
        return YuanqiWorkflowInvocation(
            workflow_key=YuanqiWorkflowKey.OUTCOME_ANALYSIS_REPORT,
            variables={
                "v_case_profile": json.dumps(
                    case_profile.model_dump(mode="json"),
                    ensure_ascii=False,
                ),
                "v_legal_support_summary": legal_support_summary,
                "v_simulation_timeline": simulation_timeline,
                "v_opponent_behavior": json.dumps(
                    opponent_behavior,
                    ensure_ascii=False,
                ),
            },
        )


def normalize_string_list(items: list[str]) -> list[str]:
    return [item.strip() for item in items if item and item.strip()]


def dedupe_text_items(items: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in normalize_string_list(items):
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def to_json_string(items: list[str]) -> str:
    return json.dumps(normalize_string_list(items), ensure_ascii=False)
