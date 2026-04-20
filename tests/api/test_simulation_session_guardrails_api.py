import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from apps.api.app.main import app


def build_case_payload() -> dict:
    return {
        "domain": "civil",
        "case_type": "private_lending",
        "title": "民间借贷纠纷",
        "summary": "原告主张被告尚欠借款未还。",
        "user_perspective_role": "claimant_side",
        "user_goals": ["simulate_trial"],
        "parties": [
            {"role": "plaintiff", "display_name": "张三"},
            {"role": "defendant", "display_name": "李四"},
        ],
        "claims": ["请求判令被告偿还借款本金及利息"],
        "core_facts": ["2025-03-01 原告向被告转账 5 万元"],
        "timeline_events": [],
        "focus_issues": ["是否存在真实借贷合意"],
        "evidence_items": [],
        "missing_evidence": ["借条原件"],
        "opponent_profile": {
            "role": "defendant",
            "display_name": "李四",
            "likely_arguments": ["否认借贷合意"],
            "likely_evidence": ["聊天记录"],
            "likely_strategies": ["拖延答辩"],
        },
        "notes": "测试 simulation 会话守卫。",
    }


def test_simulation_turn_rejects_unknown_simulation_session() -> None:
    client = TestClient(app)

    created = client.post("/api/cases", json=build_case_payload())
    case_id = created.json()["data"]["case_id"]

    response = client.post(
        f"/api/cases/{case_id}/simulate/turn",
        json={
            "simulation_id": "sim_not_exists",
            "current_stage": "prepare",
            "turn_index": 1,
            "selected_action": "进入法庭调查",
        },
    )
    body = response.json()

    assert response.status_code == 404
    assert body["success"] is False
    assert body["message"] == "simulation_not_found"
    assert body["error_code"] == "simulation_not_found"
    assert body["data"] is None


def test_simulation_turn_rejects_stale_state_and_invalid_selected_action() -> None:
    client = TestClient(app)

    created = client.post("/api/cases", json=build_case_payload())
    case_id = created.json()["data"]["case_id"]

    started = client.post(f"/api/cases/{case_id}/simulate/start")
    started_data = started.json()["data"]

    invalid_action_response = client.post(
        f"/api/cases/{case_id}/simulate/turn",
        json={
            "simulation_id": started_data["simulation_id"],
            "current_stage": started_data["current_stage"],
            "turn_index": started_data["turn_index"],
            "selected_action": "非法动作",
        },
    )
    invalid_action_body = invalid_action_response.json()

    assert invalid_action_response.status_code == 422
    assert invalid_action_body["success"] is False
    assert invalid_action_body["message"] == "invalid_selected_action"
    assert invalid_action_body["error_code"] == "invalid_selected_action"

    advanced = client.post(
        f"/api/cases/{case_id}/simulate/turn",
        json={
            "simulation_id": started_data["simulation_id"],
            "current_stage": started_data["current_stage"],
            "turn_index": started_data["turn_index"],
            "selected_action": started_data["available_actions"][-1],
        },
    )
    advanced_data = advanced.json()["data"]
    assert advanced.status_code == 200
    assert advanced_data["current_stage"] == "prepare"
    assert advanced_data["turn_index"] == 2

    stale_response = client.post(
        f"/api/cases/{case_id}/simulate/turn",
        json={
            "simulation_id": started_data["simulation_id"],
            "current_stage": started_data["current_stage"],
            "turn_index": started_data["turn_index"],
            "selected_action": started_data["available_actions"][-1],
        },
    )
    stale_body = stale_response.json()

    assert stale_response.status_code == 409
    assert stale_body["success"] is False
    assert stale_body["message"] == "simulation_state_conflict"
    assert stale_body["error_code"] == "simulation_state_conflict"
