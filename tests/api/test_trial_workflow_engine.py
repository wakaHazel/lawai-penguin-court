import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from apps.api.app.orchestrators.trial_workflow_engine import (
    advance_trial_run,
    start_trial_run,
)
from apps.api.app.schemas.case import CaseProfile
from apps.api.app.schemas.common import (
    CaseParticipantRole,
    UserGoal,
    UserPerspectiveRole,
)
from apps.api.app.schemas.common import CaseType
from apps.api.app.schemas.turn import TrialStage


def build_case(case_type: CaseType = CaseType.PRIVATE_LENDING) -> CaseProfile:
    return CaseProfile(
        case_id="case_plan_001",
        domain="civil",
        case_type=case_type,
        title="计划用例案件",
        summary="用于锁定文游工作流测试。",
        user_perspective_role=UserPerspectiveRole.CLAIMANT_SIDE,
        user_goals=[UserGoal.SIMULATE_TRIAL],
        parties=[
            {
                "role": CaseParticipantRole.PLAINTIFF,
                "display_name": "张三",
            },
            {
                "role": CaseParticipantRole.DEFENDANT,
                "display_name": "李四",
            },
        ],
        claims=["请求支持我方主张"],
        core_facts=["存在基础事实争议"],
        timeline_events=[],
        focus_issues=["争议焦点一"],
        evidence_items=[],
        missing_evidence=["缺口证据一"],
        notes="workflow engine test",
    )


def test_start_trial_run_applies_case_type_modifiers() -> None:
    run, snapshot = start_trial_run(case_profile=build_case(case_type=CaseType.LABOR_DISPUTE))

    assert run.current_node_id == "N01"
    assert snapshot.current_stage == TrialStage.PREPARE
    assert run.state.evidence_strength == 42
    assert run.state.surprise_exposure == 28
    assert snapshot.hidden_state_summary["procedure_control"] in {"中性", "占优", "明显占优"}


def test_arriving_at_checkpoint_node_creates_checkpoint() -> None:
    run, _ = start_trial_run(case_profile=build_case())

    path = [
        "confirm_claims",
        "clarify_relief",
        "fact_first",
        "note_contradiction",
        "narrow_issues",
        "chain_reinforce",
    ]

    checkpoint = None
    snapshot = None
    for choice_id in path:
        run, snapshot, checkpoint = advance_trial_run(
            case_profile=build_case(),
            current_run=run,
            selected_choice_id=choice_id,
        )

    assert snapshot is not None
    assert snapshot.node_id == "N07"
    assert checkpoint is not None
    assert checkpoint.source_node_id == "N07"
    assert snapshot.hidden_state_summary["procedure_control"] in {"占优", "明显占优"}
