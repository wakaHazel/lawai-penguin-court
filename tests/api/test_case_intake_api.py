import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def test_case_intake_endpoint_accepts_case_profile_and_returns_envelope() -> None:
    try:
        from fastapi.testclient import TestClient
        from apps.api.app.main import app
    except ModuleNotFoundError:
        pytest.fail("案件录入 FastAPI 骨架尚未创建。")

    client = TestClient(app)

    payload = {
        "domain": "civil",
        "case_type": "private_lending",
        "title": "民间借贷纠纷",
        "summary": "原告主张被告尚欠借款未还。",
        "user_perspective_role": "claimant_side",
        "user_goals": ["simulate_trial", "analyze_win_rate"],
        "parties": [
            {"role": "plaintiff", "display_name": "张三"},
            {"role": "defendant", "display_name": "李四"},
        ],
        "claims": ["请求判令被告偿还借款本金及利息"],
        "core_facts": ["2025-03-01 原告向被告转账 5 万元"],
        "timeline_events": [
            {
                "time_label": "2025-03-01",
                "event_text": "原告向被告转账 5 万元",
                "significance": "形成借贷事实基础",
                "related_evidence_ids": [],
            }
        ],
        "focus_issues": ["是否存在真实借贷合意"],
        "evidence_items": [
            {
                "name": "银行转账记录",
                "evidence_type": "transfer_record",
                "summary": "显示 5 万元转账事实",
                "source": "用户录入",
                "supports": ["是否存在真实借贷合意"],
                "risk_points": [],
                "strength": "strong",
                "is_available": True,
            }
        ],
        "missing_evidence": ["借条原件"],
        "opponent_profile": {
            "role": "defendant",
            "display_name": "李四",
            "likely_arguments": ["系代为保管款项并非借款"],
            "likely_evidence": ["聊天记录"],
            "likely_strategies": ["否认借贷合意"],
        },
        "notes": "本轮只验证案件录入骨架。",
    }

    response = client.post("/api/cases", json=payload)
    body = response.json()

    assert response.status_code == 201
    assert body["success"] is True
    assert body["error_code"] is None
    assert body["message"] == "case_intake_created"
    assert body["data"]["case_id"]
    assert body["data"]["title"] == payload["title"]
    assert body["data"]["case_type"] == payload["case_type"]
