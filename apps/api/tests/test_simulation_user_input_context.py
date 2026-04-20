from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.schemas.case import (
    CaseProfile,
    EvidenceItem,
    OpponentProfile,
    PartyProfile,
    TimelineEvent,
)
from app.schemas.common import (
    CaseDomain,
    CaseParticipantRole,
    CaseType,
    EvidenceStrength,
    EvidenceType,
    UserGoal,
    UserPerspectiveRole,
)
from app.schemas.turn import (
    SimulationActionCard,
    SimulationSnapshot,
    SimulationUserInputEntry,
    TrialStage,
)
from app.schemas.trial_workflow import HiddenStateSnapshot, TrialRunSnapshot
from app.services.backend_orchestrator import BackendOrchestrator
from app.services.yuanqi_context_store import YuanqiContextStore
from app.services.yuanqi_payload_adapter import YuanqiPayloadAdapter


class SimulationUserInputContextTests(unittest.TestCase):
    def test_payload_adapter_embeds_user_input_context(self) -> None:
        adapter = YuanqiPayloadAdapter()
        invocation = adapter.build_master_invocation(
            self._build_case_profile(),
            self._build_snapshot_with_inputs(),
            "申请核验微信原始载体",
            "[turn 1 | prepare] 庭审准备阶段启动",
        )
        request = adapter.to_chat_request(
            invocation=invocation,
            assistant_id="assistant-debug",
            user_id="case_debug:sim_debug",
        )

        self.assertEqual(
            invocation.variables["latest_user_input_text"],
            "主管要求我每天早上九点前打卡，并在群里汇报进度。",
        )
        self.assertEqual(invocation.variables["latest_user_input_type"], "fact")
        self.assertEqual(invocation.variables["latest_user_input_label"], "补充事实")
        self.assertIn("补充事实", invocation.variables["stage_user_inputs_text"])
        self.assertEqual(
            len(json.loads(invocation.variables["user_input_entries_json"])),
            2,
        )
        self.assertEqual(
            len(request.messages[0].content),
            2,
        )
        self.assertIn(
            "主管要求我每天早上九点前打卡",
            request.messages[0].content[1].text,
        )

    def test_context_store_includes_user_inputs_in_historical_dialogs(self) -> None:
        snapshot = self._build_snapshot_with_inputs()
        with patch(
            "app.services.yuanqi_context_store.list_simulation_turns_for_run",
            return_value=[snapshot],
        ):
            history = YuanqiContextStore().build_historical_dialogs("sim_debug")

        self.assertIn("[turn 2 | investigation] 法庭调查第二回合", history)
        self.assertIn("[用户补充事实] 主管要求我每天早上九点前打卡", history)
        self.assertIn("[用户补充证据] 我补交了工资转账截图", history)

    def test_backend_orchestrator_uses_latest_user_input_in_analysis(self) -> None:
        snapshot = self._build_snapshot_with_inputs()
        result = BackendOrchestrator().enrich_snapshot(
            case_profile=self._build_case_profile(),
            snapshot=snapshot,
            run=self._build_run_snapshot(),
            selected_action="申请核验微信原始载体",
            historical_dialogs="[turn 2 | investigation] 法庭调查第二回合",
            preserve_existing=False,
        )

        self.assertTrue(
            any("主管要求我每天早上九点前打卡" in item for item in result.legal_support["recommended_queries"])
        )
        self.assertTrue(
            any("主管要求我每天早上九点前打卡" in item for item in result.analysis["positive_factors"])
        )
        self.assertTrue(
            any("主管要求我每天早上九点前打卡" in item for item in result.analysis["recommended_next_actions"])
        )

    def _build_case_profile(self) -> CaseProfile:
        return CaseProfile(
            case_id="case_debug",
            domain=CaseDomain.CIVIL,
            case_type=CaseType.LABOR_DISPUTE,
            title="劳动争议调试案件",
            summary="申请人主张存在劳动关系。",
            user_perspective_role=UserPerspectiveRole.CLAIMANT_SIDE,
            user_goals=[UserGoal.SIMULATE_TRIAL],
            parties=[
                PartyProfile(role=CaseParticipantRole.PLAINTIFF, display_name="张三"),
                PartyProfile(role=CaseParticipantRole.DEFENDANT, display_name="某科技公司"),
            ],
            claims=["确认劳动关系"],
            core_facts=["接受主管管理"],
            timeline_events=[
                TimelineEvent(time_label="2025-03", event_text="申请人开始工作"),
            ],
            focus_issues=["劳动关系是否成立"],
            evidence_items=[
                EvidenceItem(
                    name="聊天记录",
                    evidence_type=EvidenceType.CHAT_RECORD,
                    summary="显示主管安排工作",
                    strength=EvidenceStrength.MEDIUM,
                )
            ],
            missing_evidence=["考勤记录"],
            opponent_profile=OpponentProfile(
                role=CaseParticipantRole.DEFENDANT,
                display_name="某科技公司",
                likely_arguments=["双方系合作关系"],
            ),
        )

    def _build_snapshot_with_inputs(self) -> SimulationSnapshot:
        return SimulationSnapshot(
            simulation_id="sim_debug",
            case_id="case_debug",
            current_stage=TrialStage.INVESTIGATION,
            turn_index=2,
            node_id="N02",
            branch_focus="劳动关系是否成立",
            scene_title="法庭调查第二回合",
            scene_text="法官开始围绕管理隶属性继续追问。",
            cg_caption="",
            court_progress="",
            pressure_shift="",
            stage_objective="",
            current_task="",
            choice_prompt="",
            hidden_state_summary={},
            speaker_role=CaseParticipantRole.JUDGE,
            available_actions=["申请核验微信原始载体"],
            action_cards=[
                SimulationActionCard(
                    choice_id="choice_1",
                    action="申请核验微信原始载体",
                    intent="固定电子证据真实性",
                    risk_tip="如原始载体缺失，会被反打",
                    emphasis="critical",
                )
            ],
            user_input_entries=[
                SimulationUserInputEntry(
                    entry_id="input_1",
                    stage=TrialStage.INVESTIGATION,
                    turn_index=1,
                    input_type="evidence",
                    label="补充证据",
                    content="我补交了工资转账截图，能够证明公司按月发放报酬。",
                    created_at="2026-04-20T22:00:00Z",
                ),
                SimulationUserInputEntry(
                    entry_id="input_2",
                    stage=TrialStage.INVESTIGATION,
                    turn_index=2,
                    input_type="fact",
                    label="补充事实",
                    content="主管要求我每天早上九点前打卡，并在群里汇报进度。",
                    created_at="2026-04-20T22:05:00Z",
                ),
            ],
        )

    def _build_run_snapshot(self) -> TrialRunSnapshot:
        return TrialRunSnapshot(
            trial_run_id="sim_debug",
            case_id="case_debug",
            current_node_id="N02",
            current_stage=TrialStage.INVESTIGATION,
            turn_index=2,
            state=HiddenStateSnapshot(
                evidence_strength=57,
                procedure_control=55,
                judge_trust=56,
                opponent_pressure=48,
                contradiction_risk=34,
                surprise_exposure=28,
                settlement_tendency=42,
            ),
            visited_node_ids=["N01", "N02"],
            selected_choice_ids=["choice_1"],
        )


if __name__ == "__main__":
    unittest.main()
