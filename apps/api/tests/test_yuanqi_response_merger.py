from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.schemas.common import CaseParticipantRole
from app.schemas.turn import SimulationSnapshot, TrialStage
from app.schemas.yuanqi import YuanqiChatCompletionResponse
from app.services.yuanqi_response_merger import YuanqiResponseMerger


class YuanqiResponseMergerTests(unittest.TestCase):
    def test_extract_result_parses_structured_text_response(self) -> None:
        response = YuanqiChatCompletionResponse.model_validate(
            {
                "id": "debug-response",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": (
                                "final out : 1. **场景标题**  \n"
                                "   庭审准备启幕  \n\n"
                                "2. **场景描述**  \n"
                                "   庄严的企鹅法庭内，气氛肃穆而沉静。法官身着法袍，神情庄重地敲响法槌。  \n\n"
                                "3. **用户可选行动**  \n"
                                "   - [1] 向法官询问具体的证据提交格式要求  \n"
                                "   - [2] 陈述原告方的初步诉求框架  \n"
                                "   - [3] 要求与被告方先进行庭外证据交换协商  \n\n"
                                "4. **一句法官提示**  \n"
                                "   在准备阶段，应聚焦于明确案件核心争议点。\n"
                                "branch name : prepare"
                            ),
                        }
                    }
                ],
            }
        )

        merger = YuanqiResponseMerger()
        result = merger.extract_result(response)

        self.assertEqual(result.branch_name, "prepare")
        self.assertEqual(result.scene["scene_title"], "庭审准备启幕")
        self.assertIn("庄严的企鹅法庭内", result.scene["scene_text"])
        self.assertEqual(len(result.scene["suggested_actions"]), 3)
        self.assertEqual(result.scene["suggested_actions"][0], "向法官询问具体的证据提交格式要求")

    def test_merge_snapshot_uses_parsed_structured_text_fields(self) -> None:
        response = YuanqiChatCompletionResponse.model_validate(
            {
                "id": "debug-response",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": (
                                "final out : 1. **场景标题**  \n"
                                "   庭审准备启幕  \n\n"
                                "2. **场景描述**  \n"
                                "   庄严的企鹅法庭内，气氛肃穆而沉静。法官身着法袍，神情庄重地敲响法槌。  \n\n"
                                "3. **用户可选行动**  \n"
                                "   - [1] 向法官询问具体的证据提交格式要求  \n"
                                "   - [2] 陈述原告方的初步诉求框架  \n\n"
                                "4. **一句法官提示**  \n"
                                "   在准备阶段，应聚焦于明确案件核心争议点。\n"
                                "branch name : prepare"
                            ),
                        }
                    }
                ],
            }
        )
        snapshot = SimulationSnapshot(
            simulation_id="sim_test",
            case_id="case_test",
            current_stage=TrialStage.PREPARE,
            turn_index=1,
            node_id="N01",
            branch_focus="劳动关系是否成立",
            scene_title="旧标题",
            scene_text="旧内容",
            cg_caption="",
            court_progress="",
            pressure_shift="",
            stage_objective="旧目标",
            current_task="旧任务",
            choice_prompt="",
            hidden_state_summary={},
            speaker_role=CaseParticipantRole.JUDGE,
            available_actions=["旧动作"],
            action_cards=[],
        )

        merger = YuanqiResponseMerger()
        merged = merger.merge_snapshot(snapshot, response)

        self.assertEqual(merged.scene_title, "庭审准备启幕")
        self.assertIn("庄严的企鹅法庭内", merged.scene_text)
        self.assertEqual(merged.yuanqi_branch_name, "prepare")
        self.assertEqual(len(merged.suggested_actions), 2)
        self.assertEqual(len(merged.action_cards), 0)


if __name__ == "__main__":
    unittest.main()
