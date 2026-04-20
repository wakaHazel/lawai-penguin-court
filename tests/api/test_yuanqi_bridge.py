import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from apps.api.app.schemas.case import CaseProfile
from apps.api.app.schemas.common import CaseParticipantRole
from apps.api.app.schemas.turn import SimulationSnapshot, TrialStage


def test_bridge_builds_real_export_contract_for_scene_and_legal_workflows() -> None:
    from apps.api.app.services.yuanqi_bridge import YuanqiBridge

    bridge = YuanqiBridge()
    case_profile = build_case_profile()

    scene_invocation = bridge.build_scene_generation_invocation(
        case_profile=case_profile,
        current_stage=TrialStage.INVESTIGATION,
        turn_index=3,
        historical_dialogs="[turn 1 | prepare] opening\n[turn 2 | prepare] plead",
    )
    legal_invocation = bridge.build_legal_retrieval_invocation(case_profile)

    assert scene_invocation.workflow_key == "courtroom_scene_generation"
    assert scene_invocation.variables == {
        "current_stage": "investigation",
        "v_case_summary": "case summary",
        "round_number": "3",
        "v_historical_dialogs": "[turn 1 | prepare] opening\n[turn 2 | prepare] plead",
    }

    assert legal_invocation.workflow_key == "legal_support_retrieval"
    assert legal_invocation.variables["case_id"] == "case_demo_001"
    assert legal_invocation.variables["case_type"] == "private_lending"
    assert json.loads(legal_invocation.variables["focus_issues_json"]) == [
        "issue 1",
        "issue 2",
    ]
    assert json.loads(legal_invocation.variables["fact_keywords_json"]) == [
        "fact 1",
        "fact 2",
        "fact 3",
        "claim 1",
        "claim 2",
    ]


def test_bridge_builds_real_export_contract_for_opponent_and_report_workflows() -> None:
    from apps.api.app.services.yuanqi_bridge import YuanqiBridge

    bridge = YuanqiBridge()
    case_profile = build_case_profile()

    opponent_invocation = bridge.build_opponent_behavior_invocation(
        case_profile=case_profile,
        current_stage=TrialStage.FINAL_STATEMENT,
        selected_action="challenge",
    )
    outcome_invocation = bridge.build_outcome_analysis_invocation(
        case_profile=case_profile,
        legal_support_summary="summary",
        simulation_timeline="[turn 1 | prepare] opening",
        opponent_behavior={
            "opponent_role": "defendant",
            "opponent_action": "deny",
        },
    )

    assert opponent_invocation.workflow_key == "opponent_behavior_simulation"
    assert opponent_invocation.variables["v_opponent_role"] == "defendant"
    assert opponent_invocation.variables["v_current_stage"] == "final_statement"
    assert opponent_invocation.variables["v_selected_action"] == "challenge"
    assert json.loads(opponent_invocation.variables["v_likely_arguments"]) == [
        "argument 1",
        "argument 2",
    ]
    assert json.loads(opponent_invocation.variables["v_focus_issues"]) == [
        "issue 1",
        "issue 2",
    ]

    assert outcome_invocation.workflow_key == "outcome_analysis_report"
    assert json.loads(outcome_invocation.variables["v_case_profile"])["case_id"] == "case_demo_001"
    assert outcome_invocation.variables["v_legal_support_summary"] == "summary"
    assert outcome_invocation.variables["v_simulation_timeline"] == "[turn 1 | prepare] opening"
    assert json.loads(outcome_invocation.variables["v_opponent_behavior"]) == {
        "opponent_role": "defendant",
        "opponent_action": "deny",
    }


def test_payload_adapter_builds_custom_variables_contract() -> None:
    from apps.api.app.services.yuanqi_payload_adapter import YuanqiPayloadAdapter

    adapter = YuanqiPayloadAdapter()
    case_profile = build_case_profile()
    snapshot = build_snapshot(stage=TrialStage.FINAL_STATEMENT, turn_index=6)

    invocation = adapter.build_master_invocation(
        case_profile=case_profile,
        snapshot=snapshot,
        selected_action="sum up",
        historical_dialogs="[turn 1 | prepare] opening\n[turn 2 | investigation] inquiry",
    )
    request_payload = adapter.to_chat_request(
        invocation=invocation,
        assistant_id="assistant_w00_demo",
        user_id="case_demo_001:sim_demo_001",
    )

    assert invocation.workflow_key == "master_orchestration"
    assert invocation.variables["current_stage"] == "debate"
    assert invocation.variables["selected_action"] == "sum up"
    assert invocation.variables["round_number"] == "6"
    assert invocation.variables["v_case_type"] == "民间借贷纠纷"
    assert invocation.variables["v_focus_issues"] == "issue 1；issue 2"
    assert invocation.variables["v_fact_keywords"] == "fact 1；fact 2；fact 3；claim 1；claim 2"
    assert invocation.variables["v_opponent_role"] == "被告方"
    assert invocation.variables["v_opponent_argument"] == "argument 1；argument 2"
    assert invocation.variables["v_opponent_arguments"] == "argument 1；argument 2"
    assert request_payload.assistant_id == "assistant_w00_demo"
    assert request_payload.user_id == "case_demo_001:sim_demo_001"
    assert request_payload.messages[0].role == "user"
    assert request_payload.messages[0].content[0].type == "text"
    assert request_payload.messages[0].content[0].text == "开始执行工作流"
    assert request_payload.custom_variables["current_stage"] == "debate"
    assert request_payload.custom_variables["v_case_summary"] == "case summary"
    assert request_payload.custom_variables["v_historical_dialogs"]


def test_response_merger_extracts_result_json_and_overlays_snapshot() -> None:
    from apps.api.app.schemas.yuanqi import YuanqiChatCompletionResponse
    from apps.api.app.services.yuanqi_response_merger import YuanqiResponseMerger

    merger = YuanqiResponseMerger()
    snapshot = build_snapshot(stage=TrialStage.DEBATE, turn_index=4)
    response = YuanqiChatCompletionResponse.model_validate(
        {
            "id": "resp_demo_001",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(
                            {
                                "status": "ok",
                                "stage": "debate",
                                "scene": {
                                    "scene_title": "new evidence",
                                    "scene_text": "the other side submits a bank slip.",
                                    "speaker_role": "defendant",
                                    "suggested_actions": ["challenge evidence", "request adjournment"],
                                    "branch_focus": "surprise_evidence",
                                    "next_stage_hint": "debate",
                                },
                                "legal_support": {
                                    "legal_support_summary": "challenge admissibility and probative value"
                                },
                                "opponent": {
                                    "opponent_role": "defendant",
                                    "opponent_action": "submit evidence",
                                    "opponent_argument": "the transfer proves no loan relationship",
                                },
                                "analysis": {
                                    "win_rate_estimate": "62%",
                                    "risk_points": ["new evidence source not verified"],
                                },
                                "degraded_flags": [],
                            },
                            ensure_ascii=False,
                        ),
                    }
                }
            ],
            "output": {
                "branch_name": "trial",
            },
        }
    )

    merged_snapshot = merger.merge_snapshot(snapshot=snapshot, response=response)

    assert merged_snapshot.current_stage == TrialStage.DEBATE
    assert merged_snapshot.scene_title == "new evidence"
    assert merged_snapshot.scene_text == "the other side submits a bank slip."
    assert merged_snapshot.speaker_role == CaseParticipantRole.DEFENDANT
    assert merged_snapshot.branch_focus == "surprise_evidence"
    assert merged_snapshot.suggested_actions == ["challenge evidence", "request adjournment"]
    assert merged_snapshot.next_stage_hint == "debate"
    assert merged_snapshot.legal_support["legal_support_summary"] == "challenge admissibility and probative value"
    assert merged_snapshot.opponent["opponent_action"] == "submit evidence"
    assert merged_snapshot.analysis["win_rate_estimate"] == "62%"
    assert merged_snapshot.yuanqi_branch_name == "trial"
    assert merged_snapshot.degraded_flags == []


def test_response_merger_accepts_markdown_fenced_json() -> None:
    from apps.api.app.schemas.yuanqi import YuanqiChatCompletionResponse
    from apps.api.app.services.yuanqi_response_merger import YuanqiResponseMerger

    merger = YuanqiResponseMerger()
    snapshot = build_snapshot(stage=TrialStage.PREPARE, turn_index=1)
    response = YuanqiChatCompletionResponse.model_validate(
        {
            "id": "resp_demo_fenced",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": """```json
{
  "status": "ok",
  "stage": "prepare",
  "scene": {
    "scene_title": "开庭",
    "scene_text": "法槌轻敲，书记员核对到庭情况。",
    "speaker_role": "judge",
    "suggested_actions": ["确认诉请", "先讲事实主线"],
    "branch_focus": "court_opening",
    "next_stage_hint": "prepare"
  },
  "legal_support": {},
  "opponent": {},
  "analysis": {},
  "degraded_flags": []
}
```""",
                    }
                }
            ],
        }
    )

    merged_snapshot = merger.merge_snapshot(snapshot=snapshot, response=response)

    assert merged_snapshot.scene_title == "开庭"
    assert merged_snapshot.branch_focus == "court_opening"
    assert merged_snapshot.suggested_actions == ["确认诉请", "先讲事实主线"]


def test_response_merger_normalizes_object_degraded_flags() -> None:
    from apps.api.app.schemas.yuanqi import YuanqiChatCompletionResponse
    from apps.api.app.services.yuanqi_response_merger import YuanqiResponseMerger

    merger = YuanqiResponseMerger()
    snapshot = build_snapshot(stage=TrialStage.PREPARE, turn_index=1)
    response = YuanqiChatCompletionResponse.model_validate(
        {
            "id": "resp_demo_object_flags",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": """```json
{
  "status": "ok",
  "stage": "prepare",
  "scene": {
    "scene_title": "开庭",
    "scene_text": "法庭核对诉请与证据准备情况。",
    "speaker_role": "judge",
    "suggested_actions": ["确认诉请"],
    "branch_focus": "court_opening",
    "next_stage_hint": "prepare"
  },
  "legal_support": {},
  "opponent": {},
  "analysis": {},
  "degraded_flags": {
    "quality_warning": false,
    "completeness_warning": true,
    "complexity_level": "中"
  }
}
```""",
                    }
                }
            ],
        }
    )

    merged_snapshot = merger.merge_snapshot(snapshot=snapshot, response=response)

    assert merged_snapshot.degraded_flags == [
        "completeness_warning",
        "complexity_level:中",
    ]


def build_case_profile() -> CaseProfile:
    return CaseProfile(
        case_id="case_demo_001",
        domain="civil",
        case_type="private_lending",
        title="loan dispute",
        summary="case summary",
        user_perspective_role="claimant_side",
        user_goals=["simulate_trial", "analyze_win_rate"],
        parties=[
            {"role": "plaintiff", "display_name": "A"},
            {"role": "defendant", "display_name": "B"},
        ],
        claims=["claim 1", "claim 2"],
        core_facts=["fact 1", "fact 2", "fact 3"],
        timeline_events=[],
        focus_issues=["issue 1", "issue 2"],
        evidence_items=[],
        missing_evidence=["missing 1"],
        opponent_profile={
            "role": "defendant",
            "display_name": "B",
            "likely_arguments": ["argument 1", "argument 2"],
            "likely_evidence": ["evidence 1"],
            "likely_strategies": ["strategy 1"],
        },
        notes="notes",
    )


def build_snapshot(stage: TrialStage, turn_index: int) -> SimulationSnapshot:
    return SimulationSnapshot(
        simulation_id="sim_demo_001",
        case_id="case_demo_001",
        current_stage=stage,
        turn_index=turn_index,
        node_id="N99",
        branch_focus="general",
        scene_title="scene",
        scene_text="scene text",
        cg_caption="",
        court_progress="",
        pressure_shift="",
        choice_prompt="",
        hidden_state_summary={},
        speaker_role=CaseParticipantRole.JUDGE,
        available_actions=["choice 1"],
        workflow_hints=[],
    )
