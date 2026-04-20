import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_simulation_history_and_checkpoints_are_available() -> None:
    client = TestClient(app)
    case_id = create_case(client)
    started = client.post(f"/api/cases/{case_id}/simulate/start").json()["data"]

    run_turn(
        client,
        case_id,
        started["simulation_id"],
        started["current_stage"],
        started["turn_index"],
        "确认诉请",
    )
    data = client.get(f"/api/cases/{case_id}/simulate/latest").json()["data"]

    for action in [
        "明确核心请求",
        "先讲事实主线",
        "抓取答辩矛盾",
        "推动争点收束",
        "先打证据链闭环",
    ]:
        latest = run_turn(
            client,
            case_id,
            data["simulation_id"],
            data["current_stage"],
            data["turn_index"],
            action,
        )
        data = latest

    history_response = client.get(f"/api/cases/{case_id}/simulate/history")
    checkpoints_response = client.get(f"/api/cases/{case_id}/simulate/checkpoints")

    assert history_response.status_code == 200
    assert checkpoints_response.status_code == 200
    assert len(history_response.json()["data"]) >= 7
    assert checkpoints_response.json()["data"][0]["source_node_id"] == "N07"


def test_simulation_can_resume_from_checkpoint() -> None:
    client = TestClient(app)
    case_id = create_case(client)
    started = client.post(f"/api/cases/{case_id}/simulate/start").json()["data"]
    data = started

    for action in [
        "确认诉请",
        "明确核心请求",
        "先讲事实主线",
        "抓取答辩矛盾",
        "推动争点收束",
        "先打证据链闭环",
    ]:
        data = run_turn(
            client,
            case_id,
            data["simulation_id"],
            data["current_stage"],
            data["turn_index"],
            action,
        )

    checkpoints = client.get(f"/api/cases/{case_id}/simulate/checkpoints").json()["data"]
    checkpoint_id = checkpoints[0]["checkpoint_id"]

    resumed = client.post(
        f"/api/cases/{case_id}/simulate/checkpoints/{checkpoint_id}/resume"
    )

    assert resumed.status_code == 200
    assert resumed.json()["data"]["node_id"] == "N07"
    assert resumed.json()["data"]["current_stage"] == "evidence"


def test_simulation_history_and_checkpoints_can_be_filtered_by_run() -> None:
    client = TestClient(app)
    case_id = create_case(client)

    first_run = client.post(f"/api/cases/{case_id}/simulate/start").json()["data"]
    for action in [
        "确认诉请",
        "明确核心请求",
        "先讲事实主线",
        "抓取答辩矛盾",
        "推动争点收束",
        "先打证据链闭环",
    ]:
        first_run = run_turn(
            client,
            case_id,
            first_run["simulation_id"],
            first_run["current_stage"],
            first_run["turn_index"],
            action,
        )

    second_run = client.post(f"/api/cases/{case_id}/simulate/start").json()["data"]

    filtered_history = client.get(
        f"/api/cases/{case_id}/simulate/history",
        params={"simulation_id": second_run["simulation_id"]},
    )
    filtered_checkpoints = client.get(
        f"/api/cases/{case_id}/simulate/checkpoints",
        params={"simulation_id": first_run["simulation_id"]},
    )

    assert filtered_history.status_code == 200
    assert len(filtered_history.json()["data"]) == 1
    assert filtered_history.json()["data"][0]["simulation_id"] == second_run["simulation_id"]

    assert filtered_checkpoints.status_code == 200
    assert len(filtered_checkpoints.json()["data"]) >= 1
    assert all(
        item["trial_run_id"] == first_run["simulation_id"]
        for item in filtered_checkpoints.json()["data"]
    )


def run_turn(
    client: TestClient,
    case_id: str,
    simulation_id: str,
    current_stage: str,
    turn_index: int,
    selected_action: str,
) -> dict:
    response = client.post(
        f"/api/cases/{case_id}/simulate/turn",
        json={
            "simulation_id": simulation_id,
            "current_stage": current_stage,
            "turn_index": turn_index,
            "selected_action": selected_action,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


def create_case(client: TestClient) -> str:
    payload = {
        "domain": "civil",
        "case_type": "private_lending",
        "title": "民间借贷纠纷",
        "summary": "原告主张被告尚未偿还借款本金。",
        "user_perspective_role": "claimant_side",
        "user_goals": ["simulate_trial"],
        "parties": [
            {"role": "plaintiff", "display_name": "张三"},
            {"role": "defendant", "display_name": "李四"},
        ],
        "claims": ["请求被告偿还借款本金及逾期利息"],
        "core_facts": ["2025-03-01 原告向被告转账 50000 元。"],
        "timeline_events": [],
        "focus_issues": ["是否存在真实借贷关系"],
        "evidence_items": [],
        "missing_evidence": ["借条原件"],
        "opponent_profile": {
            "role": "defendant",
            "display_name": "李四",
            "likely_arguments": ["否认借贷关系成立"],
            "likely_evidence": ["转账用途说明"],
            "likely_strategies": ["弱化借款合意"],
        },
        "notes": "模拟推进接口回归测试",
    }

    created = client.post("/api/cases", json=payload)
    return created.json()["data"]["case_id"]
