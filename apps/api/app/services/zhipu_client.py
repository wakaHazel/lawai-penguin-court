from __future__ import annotations

import json
import os
from collections import OrderedDict
from typing import Any, Callable
from uuid import uuid4
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..schemas.yuanqi import YuanqiChatCompletionRequest, YuanqiChatCompletionResponse

_DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
_DEFAULT_MODEL = "glm-4.5-air"
_DEFAULT_MAX_TOKENS = 1800
_DEFAULT_TEMPERATURE = 0.2
_JSON_RESPONSE_FORMAT = {"type": "json_object"}


class ZhipuClientError(RuntimeError):
    pass


class ZhipuClient:
    SYSTEM_PROMPT = (
        "你是“企鹅法庭”的核心庭审模拟引擎，负责生成沉浸式、真实、可执行的庭审回合节点。"
        "适用场景是中国民事诉讼语境下的庭前准备、法庭调查、举证质证、法庭辩论、最后陈述、调解或裁判结果推演。"
        "输出必须同时满足四点：法律场景真实、文游感强、动作可执行、JSON 严格可解析。"
        "只允许输出 JSON 对象，禁止 Markdown 代码块，禁止输出任何 JSON 之外的解释。"
        "顶层字段必须完整包含：status、stage、scene、legal_support、opponent、analysis、degraded_flags。"
        "status 固定输出 ok。stage 必须与输入 current_stage 保持一致。degraded_flags 默认输出空数组。"
        "scene 必须包含：scene_title、scene_text、speaker_role、suggested_actions、branch_focus、next_stage_hint、stage_objective、current_task、cg_caption、action_cards。"
        "scene_title 要像真实庭审节点标题。scene_text 要写成 2 到 4 段连续现场文本，体现法官、对方或程序推进压力。"
        "speaker_role 只能是 judge、plaintiff、defendant、clerk、witness、other 之一。"
        "suggested_actions 必须是 2 到 4 条中文短句。"
        "action_cards 必须是 2 到 4 个对象，每个对象包含 action、intent、risk_tip、emphasis。"
        "emphasis 只能是 steady 或 critical。"
        "legal_support、opponent、analysis 必须是对象，允许简洁，但不能是 null 或纯字符串。"
        "如果输入信息不足，不得编造具体法条编号、证据编号、法院观点或确定性判决结果；应保持审慎、贴合当前阶段。"
    )

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str = _DEFAULT_BASE_URL,
        model: str = _DEFAULT_MODEL,
        timeout_seconds: int = 30,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        temperature: float = _DEFAULT_TEMPERATURE,
        transport: Callable[[str, bytes, dict[str, str], int], dict[str, Any]] | None = None,
    ) -> None:
        self.api_key = (api_key or "").strip()
        self.base_url = base_url.rstrip("/")
        self.model = model.strip() or _DEFAULT_MODEL
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max(256, max_tokens)
        self.temperature = min(1.0, max(0.0, temperature))
        self._transport = transport or _default_transport

    @classmethod
    def from_env(cls) -> "ZhipuClient":
        return cls(
            api_key=os.getenv("ZHIPU_API_KEY") or os.getenv("GLM_API_KEY"),
            base_url=os.getenv("ZHIPU_BASE_URL") or os.getenv("ZHIPU_API_URL") or _DEFAULT_BASE_URL,
            model=os.getenv("ZHIPU_MODEL", _DEFAULT_MODEL),
            timeout_seconds=int(os.getenv("ZHIPU_TIMEOUT_SECONDS", "30")),
            max_tokens=int(os.getenv("ZHIPU_MAX_TOKENS", str(_DEFAULT_MAX_TOKENS))),
            temperature=float(os.getenv("ZHIPU_TEMPERATURE", str(_DEFAULT_TEMPERATURE))),
        )

    def is_enabled(self) -> bool:
        return bool(self.api_key)

    def create_turn_completion(
        self,
        request_payload: YuanqiChatCompletionRequest,
    ) -> YuanqiChatCompletionResponse:
        if not self.is_enabled():
            raise ZhipuClientError("zhipu_not_configured")

        user_content = self._build_user_prompt(request_payload)
        payload = json.dumps(
            {
                "model": self.model,
                "stream": False,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "response_format": _JSON_RESPONSE_FORMAT,
                "user_id": request_payload.user_id,
                "request_id": self._build_request_id(request_payload.user_id),
                "messages": [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
            },
            ensure_ascii=False,
        ).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            raw_response = self._transport(
                f"{self.base_url}/chat/completions",
                payload,
                headers,
                self.timeout_seconds,
            )
        except (HTTPError, URLError, TimeoutError) as exc:
            raise ZhipuClientError("zhipu_request_failed") from exc

        return YuanqiChatCompletionResponse.model_validate(raw_response)

    def _build_user_prompt(self, request_payload: YuanqiChatCompletionRequest) -> str:
        variables = self._collect_variables(request_payload)
        raw_text = self._flatten_user_content(request_payload)
        if not variables:
            return raw_text

        current_stage = str(variables.get("current_stage") or "prepare")
        structured_context = {
            "case_id": str(variables.get("case_id") or ""),
            "current_stage": current_stage,
            "selected_action": str(variables.get("selected_action") or ""),
            "round_number": str(variables.get("round_number") or "1"),
            "case_summary": str(variables.get("v_case_summary") or ""),
            "case_type": str(variables.get("v_case_type") or ""),
            "focus_issues": self._coerce_json_value(variables.get("v_focus_issues")),
            "fact_keywords": self._coerce_json_value(variables.get("v_fact_keywords")),
            "opponent_role": str(variables.get("v_opponent_role") or ""),
            "opponent_arguments": self._coerce_json_value(
                str(
                    variables.get("v_opponent_argument")
                    or variables.get("v_opponent_arguments")
                    or ""
                )
            ),
            "historical_dialogs": str(variables.get("v_historical_dialogs") or ""),
            "latest_user_input_text": str(variables.get("latest_user_input_text") or ""),
            "latest_user_input_type": str(variables.get("latest_user_input_type") or ""),
            "latest_user_input_label": str(variables.get("latest_user_input_label") or ""),
            "stage_user_inputs_text": str(variables.get("stage_user_inputs_text") or ""),
            "user_input_entries": self._coerce_json_value(
                str(variables.get("user_input_entries_json") or "[]")
            ),
        }
        return (
            "请基于以下案件上下文，生成企鹅法庭当前回合的庭审节点。\n"
            f"当前阶段要求：{self._stage_direction(current_stage)}\n"
            "输出要求：\n"
            "1. 只输出合法 JSON 对象；\n"
            "2. stage 必须与 current_stage 完全一致；\n"
            "3. scene_text 必须体现法庭现场推进、对方压力或法官关注点；\n"
            "4. suggested_actions 与 action_cards 要互相呼应，动作要具体、可点选；\n"
            "5. 如果 historical_dialogs 为空，按首轮开场生成，不得假装已经发生过多轮互动。\n"
            "案件上下文如下：\n"
            f"{json.dumps(structured_context, ensure_ascii=False, indent=2)}"
        )

    def _flatten_user_content(self, request_payload: YuanqiChatCompletionRequest) -> str:
        chunks: list[str] = []
        for message in request_payload.messages:
            for item in message.content:
                if item.type == "text" and item.text.strip():
                    chunks.append(item.text)
        return "\n".join(chunks)

    def _parse_key_value_lines(self, raw_text: str) -> OrderedDict[str, str]:
        variables: OrderedDict[str, str] = OrderedDict()
        for line in raw_text.splitlines():
            stripped = line.strip()
            if not stripped or " = " not in stripped:
                continue
            key, value = stripped.split(" = ", 1)
            key = key.strip()
            value = value.strip()
            if key:
                variables[key] = value
        return variables

    def _collect_variables(self, request_payload: YuanqiChatCompletionRequest) -> OrderedDict[str, str]:
        variables: OrderedDict[str, str] = OrderedDict()
        for key, value in request_payload.custom_variables.items():
            normalized_key = str(key).strip()
            if not normalized_key:
                continue
            variables[normalized_key] = str(value)
        if variables:
            return variables
        return self._parse_key_value_lines(self._flatten_user_content(request_payload))

    def _coerce_json_value(self, value: str | None) -> Any:
        text = (value or "").strip()
        if not text:
            return []
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    def _stage_direction(self, current_stage: str) -> str:
        directions = {
            "prepare": "突出程序准备、到庭核验、举证期限、庭前节奏控制。",
            "investigation": "突出法庭调查中的事实厘清、争点显影、法官追问与双方陈述碰撞。",
            "evidence": "突出举证质证中的证据三性、证明链闭环、突袭证据与应对动作。",
            "debate": "突出法庭辩论中的主论点压缩、法律关系定性、因果与责任分配攻防。",
            "final_statement": "突出最后陈述的收束感，只保留最关键的主张与印象点。",
            "mediation_or_judgment": "突出调解试探、裁判走向评估与结果前夜的策略判断。",
            "report_ready": "突出复盘收束、关键得失与下一步补强方向。",
        }
        return directions.get(current_stage, "突出当前阶段最重要的庭审任务与压力点。")

    def _build_request_id(self, user_id: str) -> str:
        normalized = "".join(char if char.isalnum() else "_" for char in user_id)[:48]
        return f"penguin_court_{normalized}_{uuid4().hex[:8]}"


def _default_transport(
    endpoint: str,
    payload: bytes,
    headers: dict[str, str],
    timeout_seconds: int,
) -> dict[str, Any]:
    request = Request(
        endpoint,
        data=payload,
        headers=headers,
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))
