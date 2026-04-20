from __future__ import annotations

import json
import re
from typing import Any

from ..schemas.common import CaseParticipantRole
from ..schemas.turn import SimulationActionCard, SimulationSnapshot
from ..schemas.yuanqi import YuanqiChatCompletionResponse, YuanqiMergedResult

_ROLE_SET = {role.value for role in CaseParticipantRole}


class YuanqiResponseMerger:
    """Parses Yuanqi published-agent responses and overlays them onto snapshots."""

    def merge_snapshot(
        self,
        snapshot: SimulationSnapshot,
        response: YuanqiChatCompletionResponse,
    ) -> SimulationSnapshot:
        merged = self.extract_result(response)
        scene = self._ensure_dict(merged.scene)

        return snapshot.model_copy(
            update={
                "scene_title": str(scene.get("scene_title") or snapshot.scene_title),
                "scene_text": str(scene.get("scene_text") or snapshot.scene_text),
                "cg_caption": str(scene.get("cg_caption") or snapshot.cg_caption),
                "cg_scene": self._ensure_dict(scene.get("cg_scene")) or snapshot.cg_scene,
                "speaker_role": self._normalize_role(
                    scene.get("speaker_role"),
                    snapshot.speaker_role,
                ),
                "branch_focus": str(scene.get("branch_focus") or snapshot.branch_focus),
                "stage_objective": str(
                    scene.get("stage_objective") or snapshot.stage_objective
                ),
                "current_task": str(scene.get("current_task") or snapshot.current_task),
                "suggested_actions": self._to_string_list(
                    scene.get("suggested_actions")
                ),
                "action_cards": self._to_action_cards(scene.get("action_cards"))
                or snapshot.action_cards,
                "next_stage_hint": str(scene.get("next_stage_hint") or ""),
                "legal_support": self._ensure_dict(merged.legal_support),
                "opponent": self._ensure_dict(merged.opponent),
                "analysis": self._ensure_dict(merged.analysis),
                "degraded_flags": self._to_string_list(merged.degraded_flags),
                "yuanqi_branch_name": merged.branch_name,
            }
        )

    def extract_result(
        self,
        response: YuanqiChatCompletionResponse,
    ) -> YuanqiMergedResult:
        payload = None

        if response.output is not None:
            payload = self._decode_jsonish(response.output.result_json)
            if payload is None:
                payload = self._decode_jsonish(response.output.final_out)

        if payload is None:
            message_content = self._extract_message_content(response)
            payload = self._decode_jsonish(message_content)
            if payload is None:
                payload = self._parse_structured_text_result(message_content)

        if isinstance(payload, dict) and "result_json" in payload:
            payload = self._decode_jsonish(payload.get("result_json"))
        elif isinstance(payload, dict) and "final_out" in payload:
            payload = self._decode_jsonish(payload.get("final_out"))

        if not isinstance(payload, dict):
            raise ValueError("yuanqi_response_missing_result_json")

        payload = {
            **payload,
            "degraded_flags": self._normalize_degraded_flags(payload.get("degraded_flags")),
        }

        return YuanqiMergedResult.model_validate(
            {
                **payload,
                "branch_name": (
                    response.output.branch_name
                    if response.output is not None
                    else payload.get("branch_name")
                ),
            }
        )

    def _extract_message_content(
        self,
        response: YuanqiChatCompletionResponse,
    ) -> Any:
        if not response.choices:
            return None
        return response.choices[0].message.content

    def _decode_jsonish(self, value: Any) -> Any:
        if isinstance(value, (dict, list)):
            return value
        if not isinstance(value, str):
            return None

        stripped = value.strip()
        if not stripped:
            return None

        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            fenced = self._strip_markdown_fence(stripped)
            if fenced is None:
                return None
            try:
                return json.loads(fenced)
            except json.JSONDecodeError:
                return None

    def _parse_structured_text_result(self, value: Any) -> dict[str, Any] | None:
        if not isinstance(value, str):
            return None

        raw_text = value.strip()
        if not raw_text:
            return None

        branch_name = None
        branch_match = re.search(
            r"branch\s*name\s*:\s*([a-zA-Z_]+)",
            raw_text,
            flags=re.IGNORECASE,
        )
        if branch_match is not None:
            branch_name = branch_match.group(1).strip()
            raw_text = raw_text[: branch_match.start()].strip()

        final_out_match = re.search(
            r"final\s*out\s*:\s*",
            raw_text,
            flags=re.IGNORECASE,
        )
        if final_out_match is not None:
            raw_text = raw_text[final_out_match.end() :].strip()

        sections = self._collect_text_sections(raw_text)
        if not sections:
            return None

        scene_title = self._normalize_text_block(sections.get("场景标题", []))
        scene_text = self._normalize_text_block(sections.get("场景描述", []))
        suggested_actions = self._parse_action_lines(sections.get("用户可选行动", []))
        judge_tip = self._normalize_text_block(sections.get("一句法官提示", []))

        if not scene_title and not scene_text:
            return None

        return {
            "status": "ok",
            "stage": branch_name or "",
            "branch_name": branch_name,
            "scene": {
                "scene_title": scene_title,
                "scene_text": scene_text,
                "cg_caption": scene_title,
                "stage_objective": judge_tip,
                "current_task": judge_tip,
                "suggested_actions": suggested_actions,
                "action_cards": [
                    {
                        "action": action,
                        "intent": judge_tip,
                        "risk_tip": "",
                        "emphasis": "critical" if index == 0 else "steady",
                    }
                    for index, action in enumerate(suggested_actions)
                ],
            },
            "legal_support": {},
            "opponent": {},
            "analysis": {},
            "degraded_flags": [],
        }

    def _collect_text_sections(self, raw_text: str) -> dict[str, list[str]]:
        known_headers = ("场景标题", "场景描述", "用户可选行动", "一句法官提示")
        sections: dict[str, list[str]] = {header: [] for header in known_headers}
        current_header: str | None = None

        for raw_line in raw_text.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()
            if not stripped:
                if current_header is not None:
                    sections[current_header].append("")
                continue

            matched_header = None
            for header in known_headers:
                if header in stripped:
                    matched_header = header
                    break

            if matched_header is not None:
                current_header = matched_header
                trailing = stripped.split(matched_header, 1)[1]
                trailing = trailing.replace("*", "").replace("：", "").strip(" .:-")
                if trailing:
                    sections[current_header].append(trailing)
                continue

            if current_header is not None:
                sections[current_header].append(stripped)

        if any(self._normalize_text_block(lines) for lines in sections.values()):
            return sections
        return {}

    def _normalize_text_block(self, lines: list[str]) -> str:
        paragraphs: list[str] = []
        current_paragraph: list[str] = []

        for line in lines:
            cleaned = self._clean_inline_markup(line)
            if not cleaned:
                if current_paragraph:
                    paragraphs.append(" ".join(current_paragraph).strip())
                    current_paragraph = []
                continue
            current_paragraph.append(cleaned)

        if current_paragraph:
            paragraphs.append(" ".join(current_paragraph).strip())

        return "\n\n".join(paragraph for paragraph in paragraphs if paragraph).strip()

    def _parse_action_lines(self, lines: list[str]) -> list[str]:
        actions: list[str] = []
        for line in lines:
            cleaned = self._clean_inline_markup(line)
            if not cleaned:
                continue
            cleaned = re.sub(r"^[-*]\s*", "", cleaned)
            cleaned = re.sub(r"^\[\d+\]\s*", "", cleaned)
            cleaned = re.sub(r"^\d+[.)]\s*", "", cleaned)
            cleaned = cleaned.strip()
            if cleaned:
                actions.append(cleaned)
        return actions

    def _clean_inline_markup(self, value: str) -> str:
        cleaned = value.replace("*", "").replace("`", "").strip()
        cleaned = cleaned.rstrip("：:").strip()
        return cleaned

    def _strip_markdown_fence(self, value: str) -> str | None:
        if not value.startswith("```") or not value.endswith("```"):
            return None

        lines = value.splitlines()
        if len(lines) < 3:
            return None
        if not lines[0].startswith("```") or lines[-1].strip() != "```":
            return None

        return "\n".join(lines[1:-1]).strip()

    def _ensure_dict(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _to_string_list(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        return []

    def _normalize_degraded_flags(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        if isinstance(value, dict):
            normalized: list[str] = []
            for key, item in value.items():
                key_text = str(key).strip()
                if not key_text:
                    continue
                if isinstance(item, bool):
                    if item:
                        normalized.append(key_text)
                    continue
                item_text = str(item).strip()
                if item_text:
                    normalized.append(f"{key_text}:{item_text}")
            return normalized
        return []

    def _normalize_role(
        self,
        value: Any,
        fallback: CaseParticipantRole,
    ) -> CaseParticipantRole:
        role = str(value or fallback.value).strip()
        if role in _ROLE_SET:
            return CaseParticipantRole(role)
        return fallback

    def _to_action_cards(self, value: Any) -> list[SimulationActionCard]:
        if not isinstance(value, list):
            return []

        cards: list[SimulationActionCard] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            action = str(item.get("action") or "").strip()
            if not action:
                continue
            cards.append(
                SimulationActionCard(
                    choice_id=str(item.get("choice_id") or "").strip() or None,
                    action=action,
                    intent=str(item.get("intent") or "").strip(),
                    risk_tip=str(item.get("risk_tip") or "").strip(),
                    emphasis=str(item.get("emphasis") or "steady").strip() or "steady",
                )
            )
        return cards
