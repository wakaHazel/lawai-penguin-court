import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_simulation_start_populates_backend_orchestration_without_yuanqi(monkeypatch) -> None:
    from apps.api.app.routes import simulation as simulation_route

    class DisabledYuanqiClient:
        assistant_id = ""

        def is_enabled(self) -> bool:
            return False

    monkeypatch.setattr(simulation_route, "_YUANQI_CLIENT", DisabledYuanqiClient())

    client = TestClient(app)
    case_id = create_case(client)

    response = client.post(f"/api/cases/{case_id}/simulate/start")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["legal_support"]["retrieval_mode"] in {"fallback", "direct_api"}
    assert body["data"]["legal_support"]["legal_support_summary"]
    assert body["data"]["legal_support"]["recommended_queries"]
    assert body["data"]["opponent"]["opponent_name"] == "Northwind Technology"
    assert body["data"]["opponent"]["likely_arguments"]
    assert 0 <= body["data"]["analysis"]["estimated_win_rate"] <= 100
    assert body["data"]["analysis"]["recommended_next_actions"]
    assert body["data"]["suggested_actions"]
    assert body["data"]["stage_objective"]
    assert body["data"]["current_task"]
    assert body["data"]["action_cards"]
    assert body["data"]["action_cards"][0]["intent"]
    assert body["data"]["action_cards"][0]["risk_tip"]
    assert body["data"]["next_stage_hint"]


def test_report_ready_snapshot_contains_backend_report_summary_without_yuanqi(
    monkeypatch,
) -> None:
    from apps.api.app.routes import simulation as simulation_route

    class DisabledYuanqiClient:
        assistant_id = ""

        def is_enabled(self) -> bool:
            return False

    monkeypatch.setattr(simulation_route, "_YUANQI_CLIENT", DisabledYuanqiClient())

    client = TestClient(app)
    case_id = create_case(client)
    snapshot = client.post(f"/api/cases/{case_id}/simulate/start").json()["data"]

    while snapshot["current_stage"] != "report_ready":
        response = client.post(
            f"/api/cases/{case_id}/simulate/turn",
            json={
                "simulation_id": snapshot["simulation_id"],
                "current_stage": snapshot["current_stage"],
                "turn_index": snapshot["turn_index"],
                "selected_action": snapshot["available_actions"][0],
            },
        )
        assert response.status_code == 200
        snapshot = response.json()["data"]

    assert snapshot["analysis"]["report_status"] == "ready"
    assert snapshot["analysis"]["report_overview"]
    assert snapshot["analysis"]["report_section_keys"] == [
        "header",
        "main_axis",
        "turning_points",
        "timeline",
        "evidence_risk",
        "opponent",
        "suggestions",
        "result",
    ]
    assert snapshot["analysis"]["recommended_next_actions"]
    assert snapshot["opponent"]["risk_points"]


def create_case(client: TestClient) -> str:
    payload = {
        "domain": "civil",
        "case_type": "labor_dispute",
        "title": "Unpaid compensation dispute",
        "summary": "The employee claims a labor relationship existed and wages were unpaid.",
        "user_perspective_role": "claimant_side",
        "user_goals": [
            "simulate_trial",
            "analyze_win_rate",
            "prepare_checklist",
        ],
        "parties": [
            {"role": "applicant", "display_name": "Lin Chen"},
            {"role": "respondent", "display_name": "Northwind Technology"},
        ],
        "claims": [
            "Confirm the labor relationship",
            "Order payment of unpaid compensation",
        ],
        "core_facts": [
            "The employee followed attendance rules and daily work assignments.",
            "No written labor contract was signed.",
            "The employee has chat records and transfer screenshots.",
        ],
        "timeline_events": [],
        "focus_issues": [
            "Whether the labor relationship can be established",
            "Whether wage payment evidence is sufficient",
        ],
        "evidence_items": [
            {
                "name": "WeChat work chat",
                "evidence_type": "chat_record",
                "summary": "Shows work assignments and reporting lines.",
                "source": "user_upload",
                "supports": ["Whether the labor relationship can be established"],
                "risk_points": [],
                "strength": "medium",
                "is_available": True,
            },
            {
                "name": "Transfer screenshot",
                "evidence_type": "transfer_record",
                "summary": "Shows monthly transfers from the company account.",
                "source": "user_upload",
                "supports": ["Whether wage payment evidence is sufficient"],
                "risk_points": ["Transfer remark is not explicit payroll wording."],
                "strength": "medium",
                "is_available": True,
            },
        ],
        "missing_evidence": [
            "Attendance record",
            "Social insurance contribution record",
            "Formal HR onboarding file",
        ],
        "opponent_profile": {
            "role": "respondent",
            "display_name": "Northwind Technology",
            "likely_arguments": [
                "The parties had a cooperation relationship instead of a labor relationship.",
                "The transfers were project payments instead of wages.",
            ],
            "likely_evidence": [
                "Project settlement record",
                "Transfer record remarks",
            ],
            "likely_strategies": [
                "Deny management subordination",
                "Emphasize project-based cooperation autonomy",
            ],
        },
        "notes": "backend orchestration regression test",
    }

    response = client.post("/api/cases", json=payload)
    assert response.status_code == 201
    return response.json()["data"]["case_id"]
