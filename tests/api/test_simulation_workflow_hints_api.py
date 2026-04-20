import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_debate_stage_exposes_opponent_behavior_workflow_hint() -> None:
    client = TestClient(app)
    case_id = create_case(client)

    started = client.post(f"/api/cases/{case_id}/simulate/start")
    started_data = started.json()["data"]

    snapshot = started_data
    selected_action = ""
    while snapshot["current_stage"] != "debate":
        selected_action = snapshot["available_actions"][-1]
        snapshot = advance_with_last_action(client, case_id, snapshot)
    debate_data = snapshot

    workflow_keys = {
        item["workflow_key"] for item in debate_data["workflow_hints"]
    }
    opponent_hint = next(
        item
        for item in debate_data["workflow_hints"]
        if item["workflow_key"] == "opponent_behavior_simulation"
    )

    assert debate_data["current_stage"] == "debate"
    assert "opponent_behavior_simulation" in workflow_keys
    assert opponent_hint["variables"]["v_current_stage"] == "debate"
    assert opponent_hint["variables"]["v_selected_action"] == selected_action
    assert json.loads(opponent_hint["variables"]["v_focus_issues"]) == [
        "Whether there was a real lending agreement.",
        "Whether interest should be supported.",
    ]


def test_report_ready_stage_exposes_outcome_analysis_workflow_hint() -> None:
    client = TestClient(app)
    case_id = create_case(client)

    snapshot = client.post(f"/api/cases/{case_id}/simulate/start").json()["data"]

    while snapshot["current_stage"] != "report_ready":
        snapshot = advance_with_last_action(client, case_id, snapshot)

    workflow_keys = {
        item["workflow_key"] for item in snapshot["workflow_hints"]
    }
    outcome_hint = next(
        item
        for item in snapshot["workflow_hints"]
        if item["workflow_key"] == "outcome_analysis_report"
    )

    assert workflow_keys == {
        "courtroom_scene_generation",
        "legal_support_retrieval",
        "outcome_analysis_report",
    }
    assert json.loads(outcome_hint["variables"]["v_case_profile"])["case_id"] == case_id
    assert outcome_hint["variables"]["v_simulation_timeline"]
    assert outcome_hint["variables"]["v_legal_support_summary"] == ""
    assert json.loads(outcome_hint["variables"]["v_opponent_behavior"]) == {}


def create_case(client: TestClient) -> str:
    payload = {
        "domain": "civil",
        "case_type": "private_lending",
        "title": "Private Lending Dispute",
        "summary": "Plaintiff alleges the loan principal remains unpaid.",
        "user_perspective_role": "claimant_side",
        "user_goals": ["simulate_trial", "analyze_win_rate"],
        "parties": [
            {"role": "plaintiff", "display_name": "Alice"},
            {"role": "defendant", "display_name": "Bob"},
        ],
        "claims": [
            "Request repayment of the loan principal.",
            "Request overdue interest payment.",
        ],
        "core_facts": [
            "2025-03-01 plaintiff transferred 50000 yuan to defendant.",
        ],
        "timeline_events": [],
        "focus_issues": [
            "Whether there was a real lending agreement.",
            "Whether interest should be supported.",
        ],
        "evidence_items": [],
        "missing_evidence": ["Original IOU"],
        "opponent_profile": {
            "role": "defendant",
            "display_name": "Bob",
            "likely_arguments": ["The transfer was not a loan."],
            "likely_evidence": ["Chat records"],
            "likely_strategies": ["Deny the lending agreement."],
        },
        "notes": "Workflow hint regression test.",
    }

    created = client.post("/api/cases", json=payload)
    return created.json()["data"]["case_id"]


def advance_with_last_action(
    client: TestClient,
    case_id: str,
    snapshot: dict,
) -> dict:
    response = client.post(
        f"/api/cases/{case_id}/simulate/turn",
        json={
            "simulation_id": snapshot["simulation_id"],
            "current_stage": snapshot["current_stage"],
            "turn_index": snapshot["turn_index"],
            "selected_action": snapshot["available_actions"][-1],
        },
    )

    assert response.status_code == 200
    return response.json()["data"]
