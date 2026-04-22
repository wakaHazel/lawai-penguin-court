from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


_RUNTIME_DIR = tempfile.mkdtemp(prefix="penguin-court-test-")
os.environ["PENGUIN_RUNTIME_DATA_DIR"] = _RUNTIME_DIR
os.environ["PENGUIN_CG_MODE"] = "static"
os.environ["PENGUIN_SIMULATION_MODE"] = "live"
os.environ["PENGUIN_LIVE_PROVIDER"] = "yuanqi"


from fastapi.testclient import TestClient

from app.main import app
from app.routes import simulation as simulation_routes
from app.schemas.yuanqi import YuanqiChatCompletionResponse


def _build_live_response(current_stage: str, selected_action: str) -> YuanqiChatCompletionResponse:
    mismatched_cards = [
        {
            "action": f"外部模型建议：{current_stage}阶段改打别的点",
            "intent": f"这是故意制造的不匹配卡片，用来验证后端会回退到本地工作流动作，而不是把前端带偏。",
            "risk_tip": "若未对齐到本地节点，后续点击会触发 invalid_selected_action。",
            "emphasis": "critical",
        }
    ]
    return YuanqiChatCompletionResponse.model_validate(
        {
            "id": f"debug-{current_stage}",
            "output": {
                "branch_name": current_stage,
                "result_json": {
                    "status": "ok",
                    "stage": current_stage,
                    "scene": {
                        "scene_title": f"{current_stage}阶段实时推演",
                        "scene_text": (
                            f"【庭上动态：法庭继续围绕当前争点推进。】"
                            f"【法官发问：本轮已接收动作“{selected_action or '开始模拟'}”，请继续回应。】"
                            f"【对方动作：对方尝试借机改写争点重心。】"
                        ),
                        "speaker_role": "judge",
                        "suggested_actions": [
                            "保持当前争点不跑偏",
                            "只对最关键事实作出回应",
                        ],
                        "branch_focus": "围绕当前节点继续推进",
                        "next_stage_hint": current_stage,
                        "stage_objective": "验证 live 模式下整条链路可以持续推进。",
                        "current_task": "继续推进当前回合，并确保动作卡与节点动作保持一致。",
                        "cg_caption": f"{current_stage}阶段镜头",
                        "action_cards": mismatched_cards,
                    },
                    "legal_support": {},
                    "opponent": {},
                    "analysis": {},
                    "degraded_flags": [],
                },
            },
        }
    )


class LiveSimulationChainTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(_RUNTIME_DIR, ignore_errors=True)

    def test_live_chain_reaches_report_ready_even_when_remote_action_cards_drift(self) -> None:
        case_payload = {
            "domain": "civil",
            "case_type": "divorce_dispute",
            "title": "离婚返还彩礼链路回归测试",
            "summary": "原告主张双方婚后共同生活时间较短，要求返还彩礼及三金折价；被告则认为彩礼已用于共同生活，不应全部返还。",
            "user_perspective_role": "claimant_side",
            "user_goals": [
                "simulate_trial",
                "analyze_win_rate",
                "prepare_checklist",
                "review_evidence",
            ],
            "parties": [
                {
                    "role": "plaintiff",
                    "display_name": "张某",
                    "relation_to_case": "男方",
                    "stance_summary": "请求返还彩礼",
                },
                {
                    "role": "defendant",
                    "display_name": "李某",
                    "relation_to_case": "女方",
                    "stance_summary": "不同意全部返还",
                },
            ],
            "claims": ["返还彩礼120000元", "返还三金折价款30000元"],
            "core_facts": [
                "双方登记结婚后共同生活时间较短",
                "原告婚前向被告家庭支付彩礼并购买三金",
                "双方后续发生矛盾并长期分居",
            ],
            "timeline_events": [
                {
                    "time_label": "2024-02",
                    "event_text": "男方家庭支付彩礼",
                    "significance": "证明彩礼给付事实",
                },
                {
                    "time_label": "2024-05",
                    "event_text": "双方登记结婚并举行婚礼",
                    "significance": "影响返还比例认定",
                },
                {
                    "time_label": "2024-08",
                    "event_text": "双方分居",
                    "significance": "影响共同生活时间判断",
                },
            ],
            "focus_issues": [
                "是否符合返还彩礼的法定条件",
                "共同生活时间对返还比例的影响",
                "三金是否属于可返还范围",
            ],
            "evidence_items": [
                {
                    "name": "彩礼转账记录",
                    "evidence_type": "transfer_record",
                    "summary": "原告向被告父亲账户转账120000元",
                    "source": "银行流水",
                    "supports": ["是否符合返还彩礼的法定条件"],
                    "risk_points": ["需进一步说明系彩礼给付"],
                    "strength": "strong",
                    "is_available": True,
                }
            ],
            "missing_evidence": ["共同生活时长直接证据", "彩礼用途明细"],
            "opponent_profile": {
                "role": "defendant",
                "display_name": "李某",
                "likely_arguments": [
                    "双方已经共同生活，不符合全部返还条件",
                    "彩礼已用于共同生活和婚礼支出",
                ],
                "likely_evidence": ["婚礼照片", "共同生活开支记录"],
                "likely_strategies": ["强调共同生活事实", "压低返还比例"],
            },
            "notes": "用于验证 live 模式全链路推进。",
        }

        with TestClient(app) as client, patch.object(
            simulation_routes._YUANQI_CLIENT,
            "assistant_id",
            "assistant-debug",
        ), patch.object(
            simulation_routes._YUANQI_CLIENT,
            "is_enabled",
            return_value=True,
        ), patch.object(
            simulation_routes._YUANQI_CLIENT,
            "create_turn_completion",
            side_effect=lambda request_payload: _build_live_response(
                str(request_payload.custom_variables.get("current_stage") or "prepare"),
                str(request_payload.custom_variables.get("selected_action") or ""),
            ),
        ), patch.object(
            simulation_routes._BACKEND_ORCHESTRATOR._deli_client,
            "is_enabled",
            return_value=False,
        ), patch.object(
            simulation_routes._GEMINI_IMAGE_CLIENT,
            "is_enabled",
            return_value=False,
        ):
            create_response = client.post("/api/cases", json=case_payload)
            self.assertEqual(create_response.status_code, 201, create_response.text)
            case_id = create_response.json()["data"]["case_id"]

            start_response = client.post(f"/api/cases/{case_id}/simulate/start")
            self.assertEqual(start_response.status_code, 200, start_response.text)
            snapshot = start_response.json()["data"]

            observed_stages = [snapshot["current_stage"]]
            observed_turns = [snapshot["turn_index"]]
            self.assertTrue(snapshot["action_cards"])
            self.assertTrue(any(card.get("choice_id") for card in snapshot["action_cards"]))

            for _ in range(24):
                if snapshot["current_stage"] == "report_ready":
                    break

                first_card = next(
                    (card for card in snapshot["action_cards"] if card.get("action")),
                    None,
                )
                self.assertIsNotNone(first_card)

                turn_response = client.post(
                    f"/api/cases/{case_id}/simulate/turn",
                    json={
                        "simulation_id": snapshot["simulation_id"],
                        "current_stage": snapshot["current_stage"],
                        "turn_index": snapshot["turn_index"],
                        "selected_action": first_card["action"],
                        "selected_choice_id": first_card.get("choice_id"),
                        "user_input_entries": snapshot.get("user_input_entries", []),
                    },
                )
                self.assertEqual(turn_response.status_code, 200, turn_response.text)
                snapshot = turn_response.json()["data"]
                observed_stages.append(snapshot["current_stage"])
                observed_turns.append(snapshot["turn_index"])

                if snapshot["current_stage"] != "report_ready":
                    self.assertTrue(
                        snapshot["action_cards"],
                        f"stage {snapshot['current_stage']} should keep actionable cards",
                    )
                    self.assertTrue(
                        any(card.get("choice_id") for card in snapshot["action_cards"]),
                        f"stage {snapshot['current_stage']} should preserve canonical choice ids",
                    )

            self.assertEqual(snapshot["current_stage"], "report_ready")
            self.assertEqual(observed_turns, sorted(observed_turns))
            self.assertIn("prepare", observed_stages)
            self.assertIn("evidence", observed_stages)
            self.assertIn("debate", observed_stages)
            self.assertIn("report_ready", observed_stages)


if __name__ == "__main__":
    unittest.main()
