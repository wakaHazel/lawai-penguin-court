import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from apps.api.app.schemas.case import CaseProfile


def test_case_profile_accepts_user_perspective_and_timeline_events() -> None:
    profile = CaseProfile(
        domain="civil",
        case_type="private_lending",
        title="民间借贷纠纷",
        summary="原告主张被告尚欠借款未还。",
        user_perspective_role="claimant_side",
        parties=[
            {"role": "plaintiff", "display_name": "张三"},
            {"role": "defendant", "display_name": "李四"},
        ],
        timeline_events=[
            {
                "time_label": "2025-03-01",
                "event_text": "原告向被告转账 5 万元",
                "significance": "形成借贷事实基础",
            }
        ],
    )

    assert profile.user_perspective_role == "claimant_side"
    assert len(profile.timeline_events) == 1
    assert profile.timeline_events[0].event_text == "原告向被告转账 5 万元"


def test_case_profile_rejects_learner_as_party_role() -> None:
    with pytest.raises(ValidationError):
        CaseProfile(
            domain="civil",
            case_type="private_lending",
            title="民间借贷纠纷",
            summary="原告主张被告尚欠借款未还。",
            user_perspective_role="learner",
            parties=[
                {"role": "learner", "display_name": "错误角色"},
            ],
        )
