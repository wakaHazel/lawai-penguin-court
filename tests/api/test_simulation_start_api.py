import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_simulation_start_executes_yuanqi_w00_and_merges_result(monkeypatch) -> None:
    from apps.api.app.routes import simulation as simulation_route
    from apps.api.app.schemas.yuanqi import YuanqiChatCompletionResponse

    monkeypatch.setenv("PENGUIN_SIMULATION_MODE", "live")

    class FakeYuanqiClient:
        assistant_id = "assistant_w00_demo"

        def __init__(self) -> None:
            self.last_request = None

        def is_enabled(self) -> bool:
            return True

        def create_turn_completion(self, request):
            self.last_request = request
            return YuanqiChatCompletionResponse.model_validate(
                {
                    "id": "resp_start_001",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": json.dumps(
                                    {
                                        "status": "ok",
                                        "stage": "prepare",
                                        "scene": {
                                            "scene_title": "court start",
                                            "scene_text": "the court session begins.",
                                            "speaker_role": "judge",
                                            "suggested_actions": ["confirm filing", "ask for mediation"],
                                            "branch_focus": "opening_check",
                                            "next_stage_hint": "prepare",
                                        },
                                        "legal_support": {
                                            "legal_support_summary": "check evidence and claims first"
                                        },
                                        "opponent": {},
                                        "analysis": {},
                                        "degraded_flags": [],
                                    },
                                    ensure_ascii=False,
                                ),
                            }
                        }
                    ],
                    "output": {"branch_name": "prepare"},
                }
            )

    class DisabledZhipuClient:
        def is_enabled(self) -> bool:
            return False

    fake_client = FakeYuanqiClient()
    monkeypatch.setattr(simulation_route, "_ZHIPU_CLIENT", DisabledZhipuClient())
    monkeypatch.setattr(simulation_route, "_YUANQI_CLIENT", fake_client)

    client = TestClient(app)
    created = client.post("/api/cases", json=build_case_payload())
    case_id = created.json()["data"]["case_id"]

    response = client.post(f"/api/cases/{case_id}/simulate/start")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["message"] == "simulation_started"
    assert body["data"]["case_id"] == case_id
    assert body["data"]["scene_title"] == "court start"
    assert body["data"]["yuanqi_branch_name"] == "prepare"
    assert body["data"]["stage_objective"]
    assert body["data"]["current_task"]
    assert isinstance(body["data"]["action_cards"], list)
    assert body["data"]["action_cards"][0]["action"]
    assert body["data"]["workflow_hints"][0]["variables"]["current_stage"] == "prepare"
    assert body["data"]["workflow_hints"][0]["variables"]["round_number"] == "1"
    assert fake_client.last_request.assistant_id == "assistant_w00_demo"
    assert fake_client.last_request.messages[0].content[0].type == "text"
    assert fake_client.last_request.messages[0].content[0].text == "开始执行工作流"
    assert fake_client.last_request.custom_variables["current_stage"] == "prepare"
    assert fake_client.last_request.custom_variables["case_id"] == case_id
    assert fake_client.last_request.custom_variables["selected_action"] == "开始庭审模拟"
    assert fake_client.last_request.custom_variables["v_case_type"] == "民间借贷纠纷"


def test_simulation_start_prefers_zhipu_when_provider_is_explicit(monkeypatch) -> None:
    from apps.api.app.routes import simulation as simulation_route
    from apps.api.app.schemas.yuanqi import YuanqiChatCompletionResponse

    monkeypatch.setenv("PENGUIN_SIMULATION_MODE", "live")
    monkeypatch.setenv("PENGUIN_LIVE_PROVIDER", "zhipu")

    class FakeZhipuClient:
        def __init__(self) -> None:
            self.calls = []

        def is_enabled(self) -> bool:
            return True

        def create_turn_completion(self, request):
            self.calls.append(request)
            return YuanqiChatCompletionResponse.model_validate(
                {
                    "id": "resp_zhipu_001",
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
                                            "scene_text": "法槌轻敲，书记员核对到庭情况，庭审准备开始。",
                                            "speaker_role": "judge",
                                            "suggested_actions": ["确认诉请", "先讲事实主线"],
                                            "branch_focus": "zhipu_prepare",
                                            "next_stage_hint": "prepare",
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
            )

    class ForbiddenYuanqiClient:
        assistant_id = "should_not_be_used"

        def is_enabled(self) -> bool:
            return True

        def create_turn_completion(self, request):
            raise AssertionError("yuanqi should not be called when zhipu is enabled")

    fake_zhipu = FakeZhipuClient()
    monkeypatch.setattr(simulation_route, "_ZHIPU_CLIENT", fake_zhipu)
    monkeypatch.setattr(simulation_route, "_YUANQI_CLIENT", ForbiddenYuanqiClient())

    client = TestClient(app)
    created = client.post("/api/cases", json=build_case_payload())
    case_id = created.json()["data"]["case_id"]

    response = client.post(f"/api/cases/{case_id}/simulate/start")
    body = response.json()

    assert response.status_code == 200
    assert body["data"]["scene_title"] == "智谱开场"
    assert body["data"]["branch_focus"] == "zhipu_prepare"
    assert len(fake_zhipu.calls) == 1


def build_case_payload() -> dict:
    return {
        "domain": "civil",
        "case_type": "private_lending",
        "title": "loan dispute",
        "summary": "borrower has not repaid principal and interest.",
        "user_perspective_role": "claimant_side",
        "user_goals": ["simulate_trial"],
        "parties": [
            {"role": "plaintiff", "display_name": "A"},
            {"role": "defendant", "display_name": "B"},
        ],
        "claims": ["repay principal"],
        "core_facts": ["transfer of 50000"],
        "timeline_events": [],
        "focus_issues": ["loan relationship"],
        "evidence_items": [],
        "missing_evidence": ["bank statement"],
        "opponent_profile": {
            "role": "defendant",
            "display_name": "B",
            "likely_arguments": ["not a loan"],
            "likely_evidence": ["memo"],
            "likely_strategies": ["deny relationship"],
        },
        "notes": "notes",
    }
