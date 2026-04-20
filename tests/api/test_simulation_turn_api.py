import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_simulation_turn_advances_and_merges_yuanqi_scene(monkeypatch) -> None:
    from apps.api.app.routes import simulation as simulation_route
    from apps.api.app.schemas.yuanqi import YuanqiChatCompletionResponse

    monkeypatch.setenv("PENGUIN_SIMULATION_MODE", "live")

    class FakeYuanqiClient:
        assistant_id = "assistant_w00_demo"

        def __init__(self) -> None:
            self.calls = []

        def is_enabled(self) -> bool:
            return True

        def create_turn_completion(self, request):
            self.calls.append(request)
            current_stage = self._extract_stage(request)
            branch_name = "prepare" if current_stage == "prepare" else "trial"
            return YuanqiChatCompletionResponse.model_validate(
                {
                    "id": f"resp_{len(self.calls)}",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": json.dumps(
                                    {
                                        "status": "ok",
                                        "stage": current_stage,
                                        "scene": {
                                            "scene_title": "yuanqi turn",
                                            "scene_text": "the published assistant returned content.",
                                            "speaker_role": "judge",
                                            "suggested_actions": ["continue", "raise evidence"],
                                            "branch_focus": "yuanqi_turn",
                                            "next_stage_hint": current_stage,
                                        },
                                        "legal_support": {
                                            "legal_support_summary": "use existing evidence and claims"
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
                    "output": {"branch_name": branch_name},
                }
            )

        def _extract_stage(self, request) -> str:
            return str(request.custom_variables.get("current_stage") or "")

    class DisabledZhipuClient:
        def is_enabled(self) -> bool:
            return False

    fake_client = FakeYuanqiClient()
    monkeypatch.setattr(simulation_route, "_ZHIPU_CLIENT", DisabledZhipuClient())
    monkeypatch.setattr(simulation_route, "_YUANQI_CLIENT", fake_client)

    client = TestClient(app)
    case_id = create_case(client)
    started_data = client.post(f"/api/cases/{case_id}/simulate/start").json()["data"]

    response = client.post(
        f"/api/cases/{case_id}/simulate/turn",
        json={
            "simulation_id": started_data["simulation_id"],
            "current_stage": started_data["current_stage"],
            "turn_index": started_data["turn_index"],
            "selected_action": started_data["available_actions"][0],
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["message"] == "simulation_turn_advanced"
    assert body["data"]["current_stage"] == "prepare"
    assert body["data"]["turn_index"] == 2
    assert body["data"]["scene_title"] == "yuanqi turn"
    assert body["data"]["branch_focus"] == "yuanqi_turn"
    assert body["data"]["yuanqi_branch_name"] == "prepare"
    assert body["data"]["stage_objective"]
    assert body["data"]["current_task"]
    assert body["data"]["action_cards"][0]["action"] == body["data"]["available_actions"][0]
    assert fake_client.calls[-1].messages[0].content[0].type == "text"
    assert fake_client.calls[-1].messages[0].content[0].text == "开始执行工作流"
    assert fake_client.calls[-1].custom_variables["selected_action"] == started_data["available_actions"][0]


def test_simulation_turn_uses_real_hint_contract_after_stage_change() -> None:
    client = TestClient(app)
    case_id = create_case(client)

    prepare_data = client.post(f"/api/cases/{case_id}/simulate/start").json()["data"]
    investigation_data = client.post(
        f"/api/cases/{case_id}/simulate/turn",
        json={
            "simulation_id": prepare_data["simulation_id"],
            "current_stage": prepare_data["current_stage"],
            "turn_index": prepare_data["turn_index"],
            "selected_action": prepare_data["available_actions"][0],
        },
    ).json()["data"]

    opening = client.post(
        f"/api/cases/{case_id}/simulate/turn",
        json={
            "simulation_id": investigation_data["simulation_id"],
            "current_stage": investigation_data["current_stage"],
            "turn_index": investigation_data["turn_index"],
            "selected_action": investigation_data["available_actions"][0],
        },
    )
    body = opening.json()
    scene_hint = body["data"]["workflow_hints"][0]

    assert opening.status_code == 200
    assert body["data"]["current_stage"] == "investigation"
    assert body["data"]["node_id"] == "N03"
    assert isinstance(body["data"]["available_actions"][0], str)
    assert body["data"]["available_actions"][0]
    assert body["data"]["current_task"]
    assert body["data"]["action_cards"]
    assert scene_hint["workflow_key"] == "courtroom_scene_generation"
    assert scene_hint["variables"]["current_stage"] == "investigation"
    assert scene_hint["variables"]["round_number"] == "3"
    assert scene_hint["variables"]["v_historical_dialogs"]


def create_case(client: TestClient) -> str:
    payload = {
        "domain": "civil",
        "case_type": "private_lending",
        "title": "loan dispute",
        "summary": "borrower dispute",
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

    created = client.post("/api/cases", json=payload)
    return created.json()["data"]["case_id"]
