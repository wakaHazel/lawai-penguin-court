from __future__ import annotations

import json
import os

from ..schemas.common import CaseParticipantRole, CaseType
from ..schemas.case import CaseProfile
from ..schemas.turn import SimulationSnapshot, SimulationUserInputEntry, TrialStage
from ..schemas.yuanqi import (
    YuanqiChatCompletionRequest,
    YuanqiChatMessage,
    YuanqiMessageContentItem,
    YuanqiWorkflowInvocation,
    YuanqiWorkflowKey,
)
from .yuanqi_bridge import dedupe_text_items, normalize_string_list

_W00_STAGE_ALIAS: dict[TrialStage, str] = {
    TrialStage.PREPARE: "prepare",
    TrialStage.INVESTIGATION: "investigation",
    TrialStage.EVIDENCE: "evidence",
    TrialStage.DEBATE: "debate",
    TrialStage.FINAL_STATEMENT: "debate",
    TrialStage.MEDIATION_OR_JUDGMENT: "report_ready",
    TrialStage.REPORT_READY: "report_ready",
}

_CASE_TYPE_LABELS: dict[CaseType, str] = {
    CaseType.PRIVATE_LENDING: "民间借贷纠纷",
    CaseType.LABOR_DISPUTE: "劳动争议",
    CaseType.DIVORCE_DISPUTE: "离婚纠纷",
    CaseType.TORT_LIABILITY: "侵权责任纠纷",
}

_ROLE_LABELS: dict[CaseParticipantRole, str] = {
    CaseParticipantRole.PLAINTIFF: "原告方",
    CaseParticipantRole.DEFENDANT: "被告方",
    CaseParticipantRole.APPLICANT: "申请方",
    CaseParticipantRole.RESPONDENT: "被申请方",
    CaseParticipantRole.AGENT: "代理人",
    CaseParticipantRole.WITNESS: "证人",
    CaseParticipantRole.JUDGE: "法官",
    CaseParticipantRole.OTHER: "对方",
}

_DEFAULT_WORKFLOW_TRIGGER_TEXT = "开始执行工作流"


class YuanqiPayloadAdapter:
    """Builds real W00 invocations and published-agent request payloads."""

    def build_master_invocation(
        self,
        case_profile: CaseProfile,
        snapshot: SimulationSnapshot,
        selected_action: str,
        historical_dialogs: str,
    ) -> YuanqiWorkflowInvocation:
        fact_keywords = dedupe_text_items(case_profile.core_facts + case_profile.claims)
        opponent_arguments = (
            case_profile.opponent_profile.likely_arguments
            if case_profile.opponent_profile
            else []
        )
        normalized_selected_action = self._normalize_selected_action(selected_action)
        case_type_code = case_profile.case_type.value
        case_type_label = _CASE_TYPE_LABELS.get(case_profile.case_type, case_type_code)
        focus_issues_text = self._to_plain_string(case_profile.focus_issues)
        fact_keywords_text = self._to_plain_string(fact_keywords)
        opponent_argument_text = self._to_plain_string(opponent_arguments)
        historical_dialogs_text = historical_dialogs.strip() or "[]"
        opponent_role_code = (
            case_profile.opponent_profile.role.value
            if case_profile.opponent_profile
            else CaseParticipantRole.OTHER.value
        )
        opponent_role_label = (
            _ROLE_LABELS.get(
                case_profile.opponent_profile.role,
                case_profile.opponent_profile.role.value,
            )
            if case_profile.opponent_profile
            else _ROLE_LABELS[CaseParticipantRole.OTHER]
        )
        latest_user_input = self._get_latest_user_input(snapshot)
        stage_user_inputs = self._get_stage_user_inputs(snapshot)
        user_input_entries = self._serialize_user_input_entries(snapshot.user_input_entries)
        latest_user_input_text = latest_user_input.content if latest_user_input else ""
        latest_user_input_type = (
            latest_user_input.input_type.value if latest_user_input else ""
        )
        latest_user_input_label = latest_user_input.label if latest_user_input else ""
        stage_user_inputs_text = self._build_user_inputs_text(stage_user_inputs)

        return YuanqiWorkflowInvocation(
            workflow_key=YuanqiWorkflowKey.MASTER_ORCHESTRATION,
            variables={
                "case_id": case_profile.case_id or "",
                "simulation_id": snapshot.simulation_id,
                "current_stage": _W00_STAGE_ALIAS[snapshot.current_stage],
                "selected_action": normalized_selected_action,
                "round_number": str(snapshot.turn_index),
                "turn_index": str(snapshot.turn_index),
                "next_stage": _W00_STAGE_ALIAS[snapshot.current_stage],
                "branch_focus": snapshot.branch_focus,
                "case_type": case_type_code,
                "v_case_summary": case_profile.summary,
                "v_case_type": case_type_label,
                "v_case_title": case_profile.title or case_type_label,
                "v_notes": case_profile.notes or "",
                "v_focus_issues": focus_issues_text,
                "focus_issues_json": self._to_json_string(case_profile.focus_issues),
                "claims_json": self._to_json_string(case_profile.claims),
                "missing_evidence_json": self._to_json_string(case_profile.missing_evidence),
                "v_fact_keywords": fact_keywords_text,
                "fact_keywords_json": self._to_json_string(fact_keywords),
                "v_opponent_role": opponent_role_label,
                "opponent_role": opponent_role_code,
                "opponent_name": (
                    case_profile.opponent_profile.display_name
                    if case_profile.opponent_profile
                    else "对方当事人"
                ),
                "v_opponent_argument": opponent_argument_text,
                "v_opponent_arguments": opponent_argument_text,
                "opponent_arguments_json": self._to_json_string(opponent_arguments),
                "likely_arguments_json": self._to_json_string(opponent_arguments),
                "likely_evidence_json": self._to_json_string(
                    case_profile.opponent_profile.likely_evidence
                    if case_profile.opponent_profile
                    else []
                ),
                "likely_strategies_json": self._to_json_string(
                    case_profile.opponent_profile.likely_strategies
                    if case_profile.opponent_profile
                    else []
                ),
                "v_historical_dialogs": historical_dialogs_text,
                "latest_user_input_text": latest_user_input_text,
                "latest_user_input_type": latest_user_input_type,
                "latest_user_input_label": latest_user_input_label,
                "stage_user_inputs_text": stage_user_inputs_text,
                "stage_user_inputs_json": json.dumps(
                    self._serialize_user_input_entries(stage_user_inputs),
                    ensure_ascii=False,
                ),
                "user_input_entries_json": json.dumps(
                    user_input_entries,
                    ensure_ascii=False,
                ),
            },
        )

    def build_user_id(self, case_id: str, simulation_id: str) -> str:
        return f"{case_id}:{simulation_id}"

    def to_chat_request(
        self,
        invocation: YuanqiWorkflowInvocation,
        assistant_id: str,
        user_id: str,
    ) -> YuanqiChatCompletionRequest:
        content = [
            YuanqiMessageContentItem(
                type="text",
                text=_DEFAULT_WORKFLOW_TRIGGER_TEXT,
            )
        ]
        supplemental_user_input_text = self._build_user_input_prompt(invocation.variables)
        if supplemental_user_input_text:
            content.append(
                YuanqiMessageContentItem(
                    type="text",
                    text=supplemental_user_input_text,
                )
            )

        return YuanqiChatCompletionRequest(
            assistant_id=assistant_id,
            user_id=user_id,
            messages=[
                YuanqiChatMessage(
                    role="user",
                    content=content,
                )
            ],
            stream=False,
            custom_variables=dict(invocation.variables),
        )

    def _normalize_selected_action(self, selected_action: str) -> str:
        normalized = selected_action.strip()
        if not normalized or normalized == "__simulation_start__":
            return "开始庭审模拟"
        if normalized == "__checkpoint_resume__":
            return "从检查点恢复模拟"
        return normalized

    def _to_plain_string(self, items: list[str]) -> str:
        normalized = normalize_string_list(items)
        if not normalized:
            return ""
        if len(normalized) == 1:
            return normalized[0]
        return "；".join(normalized)

    def _to_json_string(self, items: list[str]) -> str:
        return json.dumps(normalize_string_list(items), ensure_ascii=False)

    def _get_stage_user_inputs(
        self,
        snapshot: SimulationSnapshot,
    ) -> list[SimulationUserInputEntry]:
        return [
            entry
            for entry in snapshot.user_input_entries
            if entry.stage == snapshot.current_stage
        ]

    def _get_latest_user_input(
        self,
        snapshot: SimulationSnapshot,
    ) -> SimulationUserInputEntry | None:
        stage_user_inputs = self._get_stage_user_inputs(snapshot)
        if stage_user_inputs:
            return stage_user_inputs[-1]
        if snapshot.user_input_entries:
            return snapshot.user_input_entries[-1]
        return None

    def _serialize_user_input_entries(
        self,
        entries: list[SimulationUserInputEntry],
    ) -> list[dict[str, str]]:
        serialized: list[dict[str, str]] = []
        for entry in entries:
            serialized.append(
                {
                    "entry_id": entry.entry_id,
                    "stage": entry.stage.value,
                    "turn_index": str(entry.turn_index),
                    "input_type": entry.input_type.value,
                    "label": entry.label,
                    "content": entry.content,
                    "created_at": entry.created_at,
                }
            )
        return serialized

    def _build_user_inputs_text(
        self,
        entries: list[SimulationUserInputEntry],
    ) -> str:
        if not entries:
            return ""
        return "\n".join(
            f"[{entry.label}] {entry.content}" for entry in entries if entry.content.strip()
        )

    def _build_user_input_prompt(self, variables: dict[str, str]) -> str:
        include_prompt = os.getenv(
            "PENGUIN_YUANQI_INCLUDE_SUPPLEMENTAL_PROMPT",
            "false",
        ).strip().lower() in {"1", "true", "yes", "on"}
        if not include_prompt:
            return ""

        latest_text = (variables.get("latest_user_input_text") or "").strip()
        stage_inputs_text = (variables.get("stage_user_inputs_text") or "").strip()
        if not latest_text and not stage_inputs_text:
            return ""

        latest_label = (variables.get("latest_user_input_label") or "补充输入").strip()
        sections = ["用户新增输入上下文："]
        if latest_text:
            sections.append(f"最新{latest_label}：{latest_text}")
        if stage_inputs_text:
            sections.append("当前阶段累计补充：")
            sections.append(stage_inputs_text)
        sections.append("请把这些新增内容真正吸收进当前回合推进，不要只复述。")
        return "\n".join(sections)
