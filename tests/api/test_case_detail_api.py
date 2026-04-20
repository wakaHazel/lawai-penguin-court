import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_case_detail_endpoint_returns_saved_case_profile() -> None:
    client = TestClient(app)

    payload = {
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
        "claims": ["请求返还借款"],
        "core_facts": ["存在转账记录"],
        "timeline_events": [],
        "focus_issues": ["是否存在真实借贷关系"],
        "evidence_items": [],
        "missing_evidence": [],
        "opponent_profile": {
            "role": "defendant",
            "display_name": "李四",
            "likely_arguments": [],
            "likely_evidence": [],
            "likely_strategies": [],
        },
        "notes": "测试案件详情读取。",
    }

    created = client.post("/api/cases", json=payload)
    case_id = created.json()["data"]["case_id"]

    response = client.get(f"/api/cases/{case_id}")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["message"] == "case_detail_loaded"
    assert body["data"]["case_id"] == case_id
    assert body["data"]["title"] == payload["title"]
    assert body["data"]["summary"] == payload["summary"]
