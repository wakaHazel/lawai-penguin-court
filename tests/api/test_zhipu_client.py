import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from apps.api.app.schemas.yuanqi import YuanqiChatCompletionRequest, YuanqiChatMessage, YuanqiMessageContentItem


def test_zhipu_client_builds_structured_chat_request() -> None:
    from apps.api.app.services.zhipu_client import ZhipuClient

    captured: dict[str, object] = {}

    def fake_transport(
        endpoint: str,
        payload: bytes,
        headers: dict[str, str],
        timeout_seconds: int,
    ) -> dict:
        captured["endpoint"] = endpoint
        captured["payload"] = json.loads(payload.decode("utf-8"))
        captured["headers"] = headers
        captured["timeout_seconds"] = timeout_seconds
        return {
            "id": "chatcmpl-test",
            "model": "glm-4.5-air",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(
                            {
                                "status": "ok",
                                "stage": "prepare",
                                "scene": {
                                    "scene_title": "智谱开场",
                                    "scene_text": "法槌轻敲，庭审准备开始。",
                                    "speaker_role": "judge",
                                    "suggested_actions": ["确认诉请", "先讲事实主线"],
                                    "branch_focus": "opening",
                                    "next_stage_hint": "prepare",
                                    "stage_objective": "先稳住程序节奏。",
                                    "current_task": "明确开场主轴。",
                                    "cg_caption": "法庭静场，书记员核验到庭情况。",
                                    "action_cards": [
                                        {
                                            "action": "确认诉请",
                                            "intent": "锁定我方请求边界。",
                                            "risk_tip": "若事实铺垫不够会显得过硬。",
                                            "emphasis": "steady",
                                        }
                                    ],
                                },
                                "legal_support": {},
                                "opponent": {},
                                "analysis": {},
                                "degraded_flags": [],
                            },
                            ensure_ascii=False,
                        ),
                    }
                }
            ],
        }

    client = ZhipuClient(
        api_key="test-key",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        model="glm-4.5-air",
        transport=fake_transport,
    )
    request_payload = YuanqiChatCompletionRequest(
        assistant_id="",
        user_id="case_demo_001:sim_demo_001",
        messages=[
            YuanqiChatMessage(
                role="user",
                content=[
                    YuanqiMessageContentItem(
                        type="text",
                        text=(
                            "current_stage = prepare\n"
                            "selected_action = 确认诉请\n"
                            "round_number = 1\n"
                            'v_focus_issues = ["劳动关系是否成立"]\n'
                            'v_fact_keywords = ["工资流水","考勤记录"]\n'
                            'v_opponent_arguments = ["不存在劳动关系"]\n'
                            "v_opponent_role = defendant\n"
                            "v_case_type = labor_dispute\n"
                            "v_case_summary = 未签劳动合同双倍工资争议\n"
                            "case_id = case_demo_001"
                        ),
                    )
                ],
            )
        ],
        stream=False,
    )

    response = client.create_turn_completion(request_payload)
    payload = captured["payload"]

    assert captured["endpoint"] == "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    assert captured["headers"] == {
        "Authorization": "Bearer test-key",
        "Content-Type": "application/json",
    }
    assert captured["timeout_seconds"] == 30
    assert payload["model"] == "glm-4.5-air"
    assert payload["stream"] is False
    assert payload["temperature"] == 0.2
    assert payload["max_tokens"] == 1800
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["user_id"] == "case_demo_001:sim_demo_001"
    assert re.match(r"^penguin_court_case_demo_001_sim_demo_001_[0-9a-f]{8}$", payload["request_id"])
    assert payload["messages"][0] == {
        "role": "system",
        "content": ZhipuClient.SYSTEM_PROMPT,
    }
    assert payload["messages"][1]["role"] == "user"
    user_prompt = payload["messages"][1]["content"]
    assert "当前阶段要求：突出程序准备、到庭核验、举证期限、庭前节奏控制。" in user_prompt
    assert '"current_stage": "prepare"' in user_prompt
    assert '"selected_action": "确认诉请"' in user_prompt
    assert '"focus_issues": [' in user_prompt
    assert '"劳动关系是否成立"' in user_prompt
    assert response.choices[0].message.content


def test_zhipu_client_build_user_prompt_handles_raw_text_without_variables() -> None:
    from apps.api.app.services.zhipu_client import ZhipuClient

    client = ZhipuClient(api_key="test-key")
    request_payload = YuanqiChatCompletionRequest(
        assistant_id="",
        user_id="demo",
        messages=[
            YuanqiChatMessage(
                role="user",
                content=[YuanqiMessageContentItem(type="text", text="你好，请开始模拟。")],
            )
        ],
        stream=False,
    )

    assert client._build_user_prompt(request_payload) == "你好，请开始模拟。"


def test_zhipu_client_reads_env_defaults(monkeypatch) -> None:
    from apps.api.app.services.zhipu_client import ZhipuClient

    monkeypatch.setenv("ZHIPU_API_KEY", "env-key")
    monkeypatch.delenv("ZHIPU_API_URL", raising=False)
    monkeypatch.delenv("ZHIPU_BASE_URL", raising=False)
    monkeypatch.delenv("ZHIPU_MODEL", raising=False)
    monkeypatch.delenv("ZHIPU_MAX_TOKENS", raising=False)
    monkeypatch.delenv("ZHIPU_TEMPERATURE", raising=False)

    client = ZhipuClient.from_env()

    assert client.api_key == "env-key"
    assert client.base_url == "https://open.bigmodel.cn/api/paas/v4"
    assert client.model == "glm-4.5-air"
    assert client.max_tokens == 1800
    assert client.temperature == 0.2
    assert client.is_enabled() is True
