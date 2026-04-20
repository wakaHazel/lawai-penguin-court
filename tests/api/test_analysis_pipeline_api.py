import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_opponent_behavior_snapshot_endpoint_returns_expected_shape() -> None:
    client = TestClient(app)
    case_id, simulation_id = create_case_and_simulation(client)

    response = client.post(
        f"/api/cases/{case_id}/opponent-behavior/snapshot",
        json={"simulation_id": simulation_id},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["message"] == "opponent_behavior_snapshot_ready"
    assert body["data"]["case_id"] == case_id
    assert body["data"]["simulation_id"] == simulation_id
    assert body["data"]["likely_arguments"]
    assert body["data"]["recommended_responses"]
    assert body["data"]["risk_points"]
    assert 0 <= body["data"]["confidence"] <= 1


def test_win_rate_analysis_endpoint_returns_expected_shape() -> None:
    client = TestClient(app)
    case_id, simulation_id = create_case_and_simulation(client)

    response = client.post(
        f"/api/cases/{case_id}/win-rate/analyze",
        json={"simulation_id": simulation_id},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["message"] == "win_rate_analysis_ready"
    assert body["data"]["case_id"] == case_id
    assert body["data"]["simulation_id"] == simulation_id
    assert 0 <= body["data"]["estimated_win_rate"] <= 100
    assert 0 <= body["data"]["confidence"] <= 1
    assert isinstance(body["data"]["positive_factors"], list)
    assert isinstance(body["data"]["negative_factors"], list)


def test_replay_report_endpoint_returns_expected_shape() -> None:
    client = TestClient(app)
    case_id, simulation_id = create_case_and_simulation(
        client,
        auto_advance_steps=6,
    )

    response = client.post(
        f"/api/cases/{case_id}/replay-report/generate",
        json={"simulation_id": simulation_id},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["message"] == "replay_report_ready"
    assert body["data"]["case_id"] == case_id
    assert body["data"]["simulation_id"] == simulation_id
    assert body["data"]["report_title"]
    assert body["data"]["stage_path"]
    assert body["data"]["branch_decisions"]
    assert body["data"]["state_summary"]
    assert len(body["data"]["report_sections"]) == 8
    assert [section["key"] for section in body["data"]["report_sections"]] == [
        "header",
        "main_axis",
        "turning_points",
        "timeline",
        "evidence_risk",
        "opponent",
        "suggestions",
        "result",
    ]
    assert body["data"]["report_markdown"].startswith("# ")


def test_latest_analysis_endpoints_return_generated_run_artifacts() -> None:
    client = TestClient(app)
    case_id, simulation_id = create_case_and_simulation(
        client,
        auto_advance_steps=6,
    )

    opponent_response = client.post(
        f"/api/cases/{case_id}/opponent-behavior/snapshot",
        json={"simulation_id": simulation_id},
    )
    win_rate_response = client.post(
        f"/api/cases/{case_id}/win-rate/analyze",
        json={"simulation_id": simulation_id},
    )
    replay_response = client.post(
        f"/api/cases/{case_id}/replay-report/generate",
        json={"simulation_id": simulation_id},
    )

    assert opponent_response.status_code == 200
    assert win_rate_response.status_code == 200
    assert replay_response.status_code == 200

    latest_opponent_response = client.get(
        f"/api/cases/{case_id}/opponent-behavior/latest"
    )
    latest_win_rate_response = client.get(f"/api/cases/{case_id}/win-rate/latest")
    latest_replay_response = client.get(
        f"/api/cases/{case_id}/replay-report/latest"
    )

    assert latest_opponent_response.status_code == 200
    assert latest_opponent_response.json()["data"]["simulation_id"] == simulation_id

    assert latest_win_rate_response.status_code == 200
    assert latest_win_rate_response.json()["data"]["simulation_id"] == simulation_id

    assert latest_replay_response.status_code == 200
    assert latest_replay_response.json()["data"]["simulation_id"] == simulation_id


def create_case_and_simulation(
    client: TestClient,
    actions: list[str] | None = None,
    auto_advance_steps: int = 0,
) -> tuple[str, str]:
    payload = {
        "domain": "civil",
        "case_type": "labor_dispute",
        "title": "Labor dispute for unpaid compensation",
        "summary": "Applicant alleges labor relation exists and salary remains unpaid.",
        "user_perspective_role": "claimant_side",
        "user_goals": ["simulate_trial", "analyze_win_rate"],
        "parties": [
            {"role": "applicant", "display_name": "Employee"},
            {"role": "respondent", "display_name": "Company"},
        ],
        "claims": ["Confirm labor relation", "Pay unpaid compensation"],
        "core_facts": [
            "Applicant worked for company under attendance management.",
            "No written labor contract was signed.",
        ],
        "timeline_events": [],
        "focus_issues": ["Whether labor relation can be established"],
        "evidence_items": [
            {
                "name": "Chat records",
                "evidence_type": "chat_record",
                "summary": "Work instructions in company group.",
                "source": "user_upload",
                "supports": ["Whether labor relation can be established"],
                "risk_points": [],
                "strength": "medium",
                "is_available": True,
            }
        ],
        "missing_evidence": ["Attendance records", "Social insurance records"],
        "opponent_profile": {
            "role": "respondent",
            "display_name": "Company",
            "likely_arguments": ["No management subordination"],
            "likely_evidence": ["Project settlement records"],
            "likely_strategies": ["Deny labor relation"],
        },
        "notes": "analysis api regression test",
    }

    case_response = client.post("/api/cases", json=payload)
    case_id = case_response.json()["data"]["case_id"]

    simulation_response = client.post(f"/api/cases/{case_id}/simulate/start")
    simulation = simulation_response.json()["data"]

    if actions:
        for action in actions:
            next_response = client.post(
                f"/api/cases/{case_id}/simulate/turn",
                json={
                    "simulation_id": simulation["simulation_id"],
                    "current_stage": simulation["current_stage"],
                    "turn_index": simulation["turn_index"],
                    "selected_action": action,
                },
            )
            assert next_response.status_code == 200
            simulation = next_response.json()["data"]

    for _ in range(auto_advance_steps):
        selected_action = simulation["available_actions"][0]
        next_response = client.post(
            f"/api/cases/{case_id}/simulate/turn",
            json={
                "simulation_id": simulation["simulation_id"],
                "current_stage": simulation["current_stage"],
                "turn_index": simulation["turn_index"],
                "selected_action": selected_action,
            },
        )
        assert next_response.status_code == 200
        simulation = next_response.json()["data"]

    return case_id, simulation["simulation_id"]
