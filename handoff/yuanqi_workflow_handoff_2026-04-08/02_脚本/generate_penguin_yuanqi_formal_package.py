import copy
import json
import shutil
import time
import uuid
import zipfile
import ast
from pathlib import Path
from textwrap import dedent
from xml.sax.saxutils import escape


ROOT = Path(r"E:\lawai")
EXPORTS_DIR = ROOT / "exports"
BASE_PACKAGE_DIR = EXPORTS_DIR / "penguin_yuanqi_pkg_ascii"
BASE_WORKFLOW_PATH = BASE_PACKAGE_DIR / "0390556e-452b-4cda-8015-805512a61cc7_workflow.json"

FORMAL_DIR = EXPORTS_DIR / "企鹅法庭元器导入包_正式版"
FORMAL_ZIP = EXPORTS_DIR / "企鹅法庭元器导入包_正式版.zip"
ASCII_DIR = EXPORTS_DIR / "penguin_yuanqi_formal_pkg_ascii"
ASCII_ZIP = EXPORTS_DIR / "penguin_yuanqi_formal_pkg_ascii.zip"

DEFAULT_STRING_TYPE = "STRING"
DEFAULT_START_PARAM_KIND = "START"
OBJECT_LIKE_NORMALIZE_FIELDS = {
    "focus_issues",
    "claims",
    "missing_evidence",
    "opponent_arguments",
    "likely_arguments",
    "likely_evidence",
    "likely_strategies",
    "fact_keywords",
}
SYSTEM_QUERY_ALIASES = ("RewriteQuery", "rewritequery", "userquery", "query", "user_input")

START_PARAM_SPECS = {
    "W00": [
        ("case_id", "案件ID", "CASE-001"),
        ("simulation_id", "模拟ID", "SIM-001"),
        ("current_stage", "当前阶段", "prepare"),
        ("turn_index", "回合序号", "1"),
        ("selected_action", "上一动作", "submit_evidence"),
        ("branch_focus", "当前焦点", "劳动关系是否成立"),
        ("case_type", "案件类型", "劳动争议"),
        ("v_case_type", "展示案件类型", "劳动争议"),
        ("v_case_title", "案件标题", "未签劳动合同双倍工资争议"),
        ("v_case_summary", "案件摘要", "申请人主张与公司存在劳动关系并请求支付双倍工资差额。"),
        ("v_notes", "补充备注", "申请人已掌握部分微信记录和转账截图。"),
        ("focus_issues_json", "争议焦点JSON字符串", '["劳动关系是否成立","工资支付证据是否充分"]'),
        ("claims_json", "诉求JSON字符串", '["确认劳动关系","支付未签劳动合同双倍工资差额"]'),
        ("missing_evidence_json", "缺失证据JSON字符串", '["工资流水","考勤记录","社保缴纳记录"]'),
        ("fact_keywords_json", "事实关键词JSON字符串", '["工资流水","考勤记录","微信工作群记录"]'),
        ("opponent_arguments_json", "对方观点JSON字符串", '["双方系合作关系，不存在劳动关系"]'),
        ("opponent_role", "对方角色", "defendant"),
        ("opponent_name", "对方名称", "某科技公司"),
        ("likely_arguments_json", "对方可能主张JSON字符串", '["双方系劳务合作"]'),
        ("likely_evidence_json", "对方可能证据JSON字符串", '["合作协议","项目结算记录"]'),
        ("likely_strategies_json", "对方可能策略JSON字符串", '["否认劳动关系","弱化管理从属性"]'),
    ],
    "W01": [
        ("case_id", "案件ID", "CASE-001"),
        ("current_stage", "当前阶段", "prepare"),
        ("turn_index", "回合序号", "1"),
        ("selected_action", "上一动作", "submit_claim"),
        ("next_stage", "下一阶段", "investigation"),
        ("branch_focus", "当前焦点", "劳动关系是否成立"),
        ("v_case_type", "展示案件类型", "劳动争议"),
        ("v_case_title", "案件标题", "未签劳动合同双倍工资争议"),
        ("v_case_summary", "案件摘要", "申请人主张与公司存在劳动关系并请求支付双倍工资差额。"),
        ("v_notes", "补充备注", "申请人已掌握部分微信记录和转账截图。"),
        ("focus_issues_json", "争议焦点JSON字符串", '["劳动关系是否成立","工资支付证据是否充分"]'),
        ("claims_json", "诉求JSON字符串", '["确认劳动关系","支付未签劳动合同双倍工资差额"]'),
        ("missing_evidence_json", "缺失证据JSON字符串", '["工资流水","考勤记录","社保缴纳记录"]'),
        ("opponent_arguments_json", "对方观点JSON字符串", '["双方系合作关系，不存在劳动关系"]'),
    ],
    "W02": [
        ("case_id", "案件ID", "CASE-001"),
        ("case_type", "案件类型", "劳动争议"),
        ("focus_issues_json", "争议焦点JSON字符串", '["劳动关系是否成立","工资支付证据是否充分"]'),
        ("fact_keywords_json", "事实关键词JSON字符串", '["工资流水","考勤记录","微信工作群记录"]'),
    ],
    "W03": [
        ("case_id", "案件ID", "CASE-001"),
        ("current_stage", "当前阶段", "debate"),
        ("selected_action", "上一动作", "respond_to_defense"),
        ("branch_focus", "当前焦点", "劳动关系是否成立"),
        ("opponent_role", "对方角色", "defendant"),
        ("opponent_name", "对方名称", "某科技公司"),
        ("focus_issues_json", "争议焦点JSON字符串", '["劳动关系是否成立","工资支付证据是否充分"]'),
        ("claims_json", "诉求JSON字符串", '["确认劳动关系","支付未签劳动合同双倍工资差额"]'),
        ("likely_arguments_json", "对方可能主张JSON字符串", '["双方系劳务合作","不存在管理从属性"]'),
        ("likely_evidence_json", "对方可能证据JSON字符串", '["合作协议","项目结算记录"]'),
        ("likely_strategies_json", "对方可能策略JSON字符串", '["否认劳动关系","强调项目合作自主性"]'),
        ("legal_support_summary", "法律支持摘要", "建议围绕管理从属性、工资支付事实和书面劳动合同义务组织回应。"),
    ],
    "W04": [
        ("case_id", "案件ID", "CASE-001"),
        ("case_type", "案件类型", "劳动争议"),
        ("current_stage", "当前阶段", "report_ready"),
        ("turn_index", "回合序号", "3"),
        ("branch_focus", "当前焦点", "劳动关系是否成立"),
        ("focus_issues_json", "争议焦点JSON字符串", '["劳动关系是否成立","工资支付证据是否充分"]'),
        ("claims_json", "诉求JSON字符串", '["确认劳动关系","支付未签劳动合同双倍工资差额"]'),
        ("missing_evidence_json", "缺失证据JSON字符串", '["工资流水","考勤记录","社保缴纳记录"]'),
        ("opponent_arguments_json", "对方观点JSON字符串", '["双方系合作关系，不存在劳动关系"]'),
        ("legal_support_summary", "法律支持摘要", "建议围绕管理从属性、工资支付事实和书面劳动合同义务组织回应。"),
        ("recommended_laws_json", "推荐法源JSON字符串", '[{"name":"劳动合同法","article":"第十条","reason":"规范订立书面劳动合同义务"}]'),
        ("recommended_cases_json", "推荐案例JSON字符串", '[{"case_name":"劳动关系确认类参考案例","reason":"可比对管理从属性认定路径"}]'),
        ("issue_mapping_json", "争点映射JSON字符串", '[{"issue":"劳动关系是否成立","support_point":"管理从属性、经济从属性、组织从属性"}]'),
        ("opponent_role", "对方角色", "defendant"),
        ("opponent_name", "对方名称", "某科技公司"),
    ],
}


W01_NORMALIZE_CODE = dedent(
    '''
    import json


    VALID_STAGES = {
        "prepare",
        "investigation",
        "evidence",
        "debate",
        "final_statement",
        "mediation_or_judgment",
        "report_ready",
    }


    def _first_not_empty(*values):
        for value in values:
            if value is None:
                continue
            if isinstance(value, str) and value.strip() == "":
                continue
            if isinstance(value, list) and len(value) == 0:
                continue
            return value
        return None


    def _to_list(value):
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return []
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
            return [s]
        return [str(value).strip()]


    def _guess_stage(value):
        stage = str(value or "").strip()
        return stage if stage in VALID_STAGES else "prepare"


    def _stage_label(stage):
        mapping = {
            "prepare": "准备阶段",
            "investigation": "调查阶段",
            "evidence": "举证质证阶段",
            "debate": "法庭辩论阶段",
            "final_statement": "最后陈述阶段",
            "mediation_or_judgment": "调解或裁判阶段",
            "report_ready": "复盘报告阶段",
        }
        return mapping.get(stage, "庭审推进阶段")


    def _default_branch_focus(stage):
        mapping = {
            "prepare": "case_intake",
            "investigation": "fact_investigation",
            "evidence": "evidence_submission",
            "debate": "evidence_argumentation",
            "final_statement": "closing_statement",
            "mediation_or_judgment": "settlement_or_judgment",
            "report_ready": "report_generation",
        }
        return mapping.get(stage, "general")


    def main(params: dict) -> dict:
        stage = _guess_stage(_first_not_empty(params.get("current_stage"), params.get("stage")))
        raw_query = str(
            _first_not_empty(
                params.get("RewriteQuery"),
                params.get("rewritequery"),
                params.get("userquery"),
                params.get("query"),
                params.get("user_input"),
            )
            or ""
        )

        case_type = str(_first_not_empty(params.get("case_type"), params.get("v_case_type")) or "")
        case_title = str(params.get("v_case_title") or "企鹅法庭模拟案件")
        case_summary = str(params.get("v_case_summary") or raw_query or "待补充案件摘要")

        focus_issues = _to_list(_first_not_empty(params.get("focus_issues_json"), params.get("focus_issues"), params.get("v_focus_issues")))
        claims = _to_list(_first_not_empty(params.get("claims_json"), params.get("claims"), params.get("v_claims")))
        missing_evidence = _to_list(_first_not_empty(params.get("missing_evidence_json"), params.get("missing_evidence"), params.get("v_missing_evidence")))
        fact_keywords = _to_list(_first_not_empty(params.get("fact_keywords_json"), params.get("fact_keywords")))

        return {
            "case_id": str(params.get("case_id") or ""),
            "simulation_id": str(params.get("simulation_id") or ""),
            "current_stage": stage,
            "stage_label": _stage_label(stage),
            "selected_action": str(params.get("selected_action") or "继续推进庭审"),
            "branch_focus": str(params.get("branch_focus") or _default_branch_focus(stage)),
            "case_type": case_type,
            "case_title": case_title,
            "case_summary": case_summary,
            "notes": str(params.get("v_notes") or ""),
            "focus_issues": focus_issues,
            "claims": claims,
            "missing_evidence": missing_evidence,
            "fact_keywords": fact_keywords or ([raw_query] if raw_query else []),
            "raw_query": raw_query,
        }
    '''
).strip()


W01_SYSTEM_PROMPT = dedent(
    '''
    你是“企鹅法庭·沉浸式庭审模拟与立法沙盘推演”中的 W01_庭审场景生成 工作流。

    你会收到一个名为 normalized 的对象，里面已经整理好了：
    - 当前庭审阶段 current_stage / stage_label
    - 案由类型、案件标题、案件摘要
    - 争议焦点、诉求、证据缺口
    - 当前用户自由问句和事实关键词

    你的任务是只做“庭审场景推进生成”，不要替代法律检索、不要输出胜诉率结论、也不要编造成熟判决结果。

    你必须只输出 JSON，且字段完整，不允许输出解释文字。

    固定 JSON 结构：
    {
      "scene_title": "当前回合标题",
      "scene_text": "面向用户展示的庭审推进描述",
      "speaker_role": "judge/plaintiff/defendant/agent/witness/other 之一",
      "suggested_actions": ["建议动作1", "建议动作2"],
      "branch_focus": "当前回合焦点标签",
      "next_stage_hint": "建议的下一阶段英文枚举",
      "judge_prompt": "主持推进语或法官提示语",
      "user_focus_points": ["我方本轮重点1", "重点2"],
      "evidence_focus": ["证据重点1", "证据重点2"],
      "hearing_points": ["推进点1", "推进点2", "推进点3"],
      "fallback_notice": ""
    }

    约束：
    - speaker_role 必须从给定枚举里选。
    - suggested_actions 只能给出“建议动作”，不要伪造系统正式可点击动作列表。
    - next_stage_hint 尽量使用以下枚举之一：
      prepare / investigation / evidence / debate / final_statement / mediation_or_judgment / report_ready
    - 内容要贴合中国法律场景，但定位是模拟推演与辅助，不要宣称构成正式法律意见。
    - 如果信息不足，也要输出保守、结构化、可继续推进的场景内容。
    '''
).strip()


W01_PACK_CODE = dedent(
    '''
    import json


    WORKFLOW_KEY = "courtroom_scene_generation"
    VALID_ROLES = {"judge", "plaintiff", "defendant", "agent", "witness", "other"}


    def _to_obj(value):
        if isinstance(value, dict):
            if "Output" in value and isinstance(value["Output"], dict):
                return value["Output"]
            return value
        if value is None:
            return {}
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return {}
            try:
                return json.loads(s)
            except Exception:
                return {}
        return {}


    def _parse_model_content(value):
        obj = _to_obj(value)
        content = obj.get("Content") if isinstance(obj, dict) else None
        if isinstance(content, dict):
            return content, False
        if isinstance(content, str):
            s = content.strip()
            if not s:
                return {}, True
            try:
                parsed = json.loads(s)
                if isinstance(parsed, dict):
                    return parsed, False
            except Exception:
                pass
        return {}, True


    def _to_list(value):
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        return []


    def _sanitize_role(value):
        role = str(value or "").strip()
        return role if role in VALID_ROLES else "judge"


    def main(params: dict) -> dict:
        normalized = _to_obj(params.get("normalized"))
        llm_obj, parse_failed = _parse_model_content(params.get("draft"))

        degraded_flags = []
        if parse_failed:
            degraded_flags.append("llm_parse_failed")

        stage = str(normalized.get("current_stage") or "prepare")
        stage_label = str(normalized.get("stage_label") or "庭审推进阶段")
        scene_title = str(llm_obj.get("scene_title") or f"{stage_label}场景推进")
        branch_focus = str(llm_obj.get("branch_focus") or normalized.get("branch_focus") or "general")
        next_stage_hint = str(llm_obj.get("next_stage_hint") or stage)
        speaker_role = _sanitize_role(llm_obj.get("speaker_role"))
        suggested_actions = _to_list(llm_obj.get("suggested_actions"))
        if not suggested_actions:
            suggested_actions = [str(normalized.get("selected_action") or "继续推进庭审")]
            degraded_flags.append("suggested_actions_fallback")

        hearing_points = _to_list(llm_obj.get("hearing_points"))
        user_focus_points = _to_list(llm_obj.get("user_focus_points"))
        evidence_focus = _to_list(llm_obj.get("evidence_focus"))
        judge_prompt = str(llm_obj.get("judge_prompt") or "")
        scene_text = str(llm_obj.get("scene_text") or "").strip()
        if not scene_text:
            scene_text = "\\n".join(
                [x for x in [judge_prompt] + hearing_points + user_focus_points + evidence_focus if x]
            ).strip()
        if not scene_text:
            scene_text = "当前信息不足，建议先补充案件事实、争议焦点和证据材料后继续推进。"
            degraded_flags.append("scene_text_fallback")

        payload = {
            "workflow_key": WORKFLOW_KEY,
            "stage": stage,
            "stage_label": stage_label,
            "scene_title": scene_title,
            "scene_text": scene_text,
            "speaker_role": speaker_role,
            "suggested_actions": suggested_actions,
            "branch_focus": branch_focus,
            "next_stage_hint": next_stage_hint,
            "judge_prompt": judge_prompt,
            "user_focus_points": user_focus_points,
            "evidence_focus": evidence_focus,
            "hearing_points": hearing_points,
            "fallback_notice": str(llm_obj.get("fallback_notice") or ""),
            "source_snapshot": normalized,
        }

        answer_text = (
            f"### {scene_title}\\n"
            f"- 当前阶段：`{stage}`\\n"
            f"- 推荐推进重点：{'；'.join(user_focus_points[:3]) if user_focus_points else '继续围绕核心争点组织表达'}\\n"
            f"- 证据关注：{'；'.join(evidence_focus[:3]) if evidence_focus else '优先补强关键证据链'}\\n"
            f"- 建议动作：{'；'.join(suggested_actions[:3])}\\n\\n"
            f"{scene_text}"
        )

        return {
            "workflow_key": WORKFLOW_KEY,
            "payload_json": json.dumps(payload, ensure_ascii=False),
            "scene_title": scene_title,
            "scene_text": scene_text,
            "speaker_role": speaker_role,
            "suggested_actions_json": json.dumps(suggested_actions, ensure_ascii=False),
            "branch_focus": branch_focus,
            "next_stage_hint": next_stage_hint,
            "answer_text": answer_text,
            "degraded_flags_json": json.dumps(degraded_flags, ensure_ascii=False),
        }
    '''
).strip()


W02_NORMALIZE_CODE = dedent(
    '''
    import json


    def _first_not_empty(*values):
        for value in values:
            if value is None:
                continue
            if isinstance(value, str) and value.strip() == "":
                continue
            if isinstance(value, list) and len(value) == 0:
                continue
            return value
        return None


    def _to_list(value):
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return []
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
            return [s]
        return [str(value).strip()]


    def main(params: dict) -> dict:
        raw_query = str(
            _first_not_empty(
                params.get("RewriteQuery"),
                params.get("rewritequery"),
                params.get("userquery"),
                params.get("query"),
                params.get("user_input"),
            )
            or ""
        )
        return {
            "case_type": str(_first_not_empty(params.get("case_type"), params.get("v_case_type")) or ""),
            "case_title": str(params.get("v_case_title") or "企鹅法庭模拟案件"),
            "case_summary": str(params.get("v_case_summary") or raw_query or "待补充案件摘要"),
            "current_stage": str(params.get("current_stage") or "prepare"),
            "focus_issues": _to_list(_first_not_empty(params.get("focus_issues_json"), params.get("focus_issues"), params.get("v_focus_issues"))),
            "claims": _to_list(_first_not_empty(params.get("claims_json"), params.get("claims"), params.get("v_claims"))),
            "missing_evidence": _to_list(_first_not_empty(params.get("missing_evidence_json"), params.get("missing_evidence"), params.get("v_missing_evidence"))),
            "fact_keywords": _to_list(_first_not_empty(params.get("fact_keywords_json"), params.get("fact_keywords"))) or ([raw_query] if raw_query else []),
            "opponent_arguments": _to_list(_first_not_empty(params.get("opponent_arguments_json"), params.get("opponent_arguments"), params.get("v_opponent_arguments"))),
            "notes": str(params.get("v_notes") or ""),
            "raw_query": raw_query,
        }
    '''
).strip()


W02_SYSTEM_PROMPT = dedent(
    '''
    你是“企鹅法庭·沉浸式庭审模拟与立法沙盘推演”中的 W02_法律支持检索 工作流。

    你会收到一个名为 normalized 的对象，包含案件摘要、争议焦点、诉求、证据缺口、事实关键词、对方可能观点等信息。

    你的任务是生成“法律支持检索结果草案”，核心是帮助后续庭审模拟与风险分析，而不是给出笼统法条科普。

    你必须只输出 JSON，不允许输出解释文字。

    固定 JSON 结构：
    {
      "legal_support_summary": "本轮法律支持摘要",
      "recommended_laws": [
        {"name": "法律名称", "article": "条文编号", "reason": "适用原因"}
      ],
      "recommended_cases": [
        {"case_name": "案例名称或案例类型", "reason": "参考理由"}
      ],
      "issue_mapping": [
        {"issue": "争点", "support_point": "法律支持要点"}
      ],
      "missing_points": ["当前仍待补强的问题1", "问题2"],
      "evidence_suggestions": ["建议补充的证据1", "证据2"],
      "court_strategy": ["庭审使用建议1", "建议2"],
      "fallback_notice": ""
    }

    约束：
    - 内容要贴近中国法律实务表达，但定位是辅助检索与模拟支持。
    - 如果具体法条难以精确确定，可以给出法律类别与适用方向，但不要留空。
    - recommended_laws、recommended_cases、issue_mapping 最多各 5 条，保持可消费性。
    - 缺乏信息时，也要输出保守、可操作的支持摘要与补强建议。
    '''
).strip()


W02_PACK_CODE = dedent(
    '''
    import json


    WORKFLOW_KEY = "legal_support_retrieval"


    def _to_obj(value):
        if isinstance(value, dict):
            if "Output" in value and isinstance(value["Output"], dict):
                return value["Output"]
            return value
        if value is None:
            return {}
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return {}
            try:
                return json.loads(s)
            except Exception:
                return {}
        return {}


    def _parse_model_content(value):
        obj = _to_obj(value)
        content = obj.get("Content") if isinstance(obj, dict) else None
        if isinstance(content, dict):
            return content, False
        if isinstance(content, str):
            s = content.strip()
            if not s:
                return {}, True
            try:
                parsed = json.loads(s)
                if isinstance(parsed, dict):
                    return parsed, False
            except Exception:
                pass
        return {}, True


    def _list(value):
        return value if isinstance(value, list) else []


    def main(params: dict) -> dict:
        normalized = _to_obj(params.get("normalized"))
        llm_obj, parse_failed = _parse_model_content(params.get("draft"))

        degraded_flags = []
        if parse_failed:
            degraded_flags.append("llm_parse_failed")

        legal_support_summary = str(llm_obj.get("legal_support_summary") or "").strip()
        if not legal_support_summary:
            legal_support_summary = "当前信息不足，建议围绕案件要件事实、举证责任和抗辩方向补充法律支持检索。"
            degraded_flags.append("summary_fallback")

        recommended_laws = _list(llm_obj.get("recommended_laws"))
        recommended_cases = _list(llm_obj.get("recommended_cases"))
        issue_mapping = _list(llm_obj.get("issue_mapping"))
        missing_points = _list(llm_obj.get("missing_points"))
        evidence_suggestions = _list(llm_obj.get("evidence_suggestions"))
        court_strategy = _list(llm_obj.get("court_strategy"))

        payload = {
            "workflow_key": WORKFLOW_KEY,
            "stage": str(normalized.get("current_stage") or "prepare"),
            "legal_support_summary": legal_support_summary,
            "recommended_laws": recommended_laws,
            "recommended_cases": recommended_cases,
            "issue_mapping": issue_mapping,
            "missing_points": missing_points,
            "evidence_suggestions": evidence_suggestions,
            "court_strategy": court_strategy,
            "fallback_notice": str(llm_obj.get("fallback_notice") or ""),
            "source_snapshot": normalized,
        }

        answer_lines = [
            "### 法律支持检索摘要",
            f"- 核心结论：{legal_support_summary}",
            f"- 推荐法源数量：{len(recommended_laws)}",
            f"- 推荐案例数量：{len(recommended_cases)}",
        ]
        if missing_points:
            answer_lines.append(f"- 待补强问题：{'；'.join(str(x) for x in missing_points[:3])}")
        if court_strategy:
            answer_lines.append(f"- 庭审使用建议：{'；'.join(str(x) for x in court_strategy[:3])}")

        answer_text = "\\n".join(answer_lines)

        return {
            "workflow_key": WORKFLOW_KEY,
            "payload_json": json.dumps(payload, ensure_ascii=False),
            "legal_support_summary": legal_support_summary,
            "recommended_laws_json": json.dumps(recommended_laws, ensure_ascii=False),
            "recommended_cases_json": json.dumps(recommended_cases, ensure_ascii=False),
            "issue_mapping_json": json.dumps(issue_mapping, ensure_ascii=False),
            "missing_points_json": json.dumps(missing_points, ensure_ascii=False),
            "answer_text": answer_text,
            "degraded_flags_json": json.dumps(degraded_flags, ensure_ascii=False),
        }
    '''
).strip()


W03_NORMALIZE_CODE = dedent(
    '''
    import json


    def _first_not_empty(*values):
        for value in values:
            if value is None:
                continue
            if isinstance(value, str) and value.strip() == "":
                continue
            if isinstance(value, list) and len(value) == 0:
                continue
            return value
        return None


    def _to_list(value):
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return []
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
            return [s]
        return [str(value).strip()]


    def main(params: dict) -> dict:
        return {
            "current_stage": str(params.get("current_stage") or "debate"),
            "case_title": str(params.get("v_case_title") or "企鹅法庭模拟案件"),
            "case_summary": str(params.get("v_case_summary") or params.get("query") or "待补充案件摘要"),
            "focus_issues": _to_list(_first_not_empty(params.get("focus_issues_json"), params.get("focus_issues"), params.get("v_focus_issues"))),
            "claims": _to_list(_first_not_empty(params.get("claims_json"), params.get("claims"), params.get("v_claims"))),
            "opponent_arguments": _to_list(_first_not_empty(params.get("opponent_arguments_json"), params.get("opponent_arguments"), params.get("v_opponent_arguments"))),
            "likely_arguments": _to_list(_first_not_empty(params.get("likely_arguments_json"), params.get("likely_arguments"))),
            "likely_evidence": _to_list(_first_not_empty(params.get("likely_evidence_json"), params.get("likely_evidence"))),
            "likely_strategies": _to_list(_first_not_empty(params.get("likely_strategies_json"), params.get("likely_strategies"))),
            "opponent_role": str(params.get("opponent_role") or "defendant"),
            "opponent_name": str(params.get("opponent_name") or "对方当事人"),
            "legal_support_summary": str(params.get("legal_support_summary") or ""),
            "notes": str(params.get("v_notes") or ""),
        }
    '''
).strip()


W03_SYSTEM_PROMPT = dedent(
    '''
    你是“企鹅法庭·沉浸式庭审模拟与立法沙盘推演”中的 W03_对方行为模拟 工作流。

    你会收到一个名为 normalized 的对象，其中包含案件摘要、争议焦点、对方既有主张、可能抗辩、可能证据、当前阶段等信息。

    你的任务是模拟“对方下一步最可能怎么出招”，用于帮助我方准备反驳，而不是夸张戏剧化表演。

    你必须只输出 JSON，不允许输出解释文字。

    固定 JSON 结构：
    {
      "opponent_role": "defendant/respondent/agent/witness/other 之一",
      "opponent_name": "对方名称",
      "opponent_action": "对方本轮最可能动作",
      "opponent_argument": ["可能论点1", "论点2"],
      "opponent_evidence": ["可能证据1", "证据2"],
      "risk_delta": "up/down/flat",
      "next_pressure": "对我方造成的下一步压力",
      "rebuttal_points": ["我方反击点1", "反击点2"],
      "judge_concern": ["法官可能关注点1", "关注点2"],
      "fallback_notice": ""
    }

    约束：
    - 输出应保持法律实务感，重点是“可能动作 + 论点 + 证据 + 压力”。
    - risk_delta 只能是 up / down / flat。
    - opponent_role 必须使用给定枚举，不得输出自然语言角色名。
    - 如果信息有限，也要给出保守、可信的模拟。
    '''
).strip()


W03_PACK_CODE = dedent(
    '''
    import json


    WORKFLOW_KEY = "opponent_behavior_simulation"
    VALID_ROLES = {"defendant", "respondent", "agent", "witness", "other"}
    VALID_RISK_DELTA = {"up", "down", "flat"}


    def _to_obj(value):
        if isinstance(value, dict):
            if "Output" in value and isinstance(value["Output"], dict):
                return value["Output"]
            return value
        if value is None:
            return {}
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return {}
            try:
                return json.loads(s)
            except Exception:
                return {}
        return {}


    def _parse_model_content(value):
        obj = _to_obj(value)
        content = obj.get("Content") if isinstance(obj, dict) else None
        if isinstance(content, dict):
            return content, False
        if isinstance(content, str):
            s = content.strip()
            if not s:
                return {}, True
            try:
                parsed = json.loads(s)
                if isinstance(parsed, dict):
                    return parsed, False
            except Exception:
                pass
        return {}, True


    def _to_list(value):
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        return []


    def _sanitize_role(value):
        role = str(value or "").strip()
        return role if role in VALID_ROLES else "defendant"


    def _sanitize_risk_delta(value):
        risk = str(value or "").strip()
        return risk if risk in VALID_RISK_DELTA else "flat"


    def main(params: dict) -> dict:
        normalized = _to_obj(params.get("normalized"))
        llm_obj, parse_failed = _parse_model_content(params.get("draft"))

        degraded_flags = []
        if parse_failed:
            degraded_flags.append("llm_parse_failed")

        opponent_role = _sanitize_role(llm_obj.get("opponent_role") or normalized.get("opponent_role"))
        opponent_name = str(llm_obj.get("opponent_name") or normalized.get("opponent_name") or "对方当事人")
        opponent_action = str(llm_obj.get("opponent_action") or "围绕现有争点提出抗辩").strip()
        opponent_argument = _to_list(llm_obj.get("opponent_argument"))
        opponent_evidence = _to_list(llm_obj.get("opponent_evidence"))
        rebuttal_points = _to_list(llm_obj.get("rebuttal_points"))
        judge_concern = _to_list(llm_obj.get("judge_concern"))
        next_pressure = str(llm_obj.get("next_pressure") or "要求我方进一步说明事实与证据链").strip()
        risk_delta = _sanitize_risk_delta(llm_obj.get("risk_delta"))

        payload = {
            "workflow_key": WORKFLOW_KEY,
            "stage": str(normalized.get("current_stage") or "debate"),
            "opponent_role": opponent_role,
            "opponent_name": opponent_name,
            "opponent_action": opponent_action,
            "opponent_argument": opponent_argument,
            "opponent_evidence": opponent_evidence,
            "risk_delta": risk_delta,
            "next_pressure": next_pressure,
            "rebuttal_points": rebuttal_points,
            "judge_concern": judge_concern,
            "fallback_notice": str(llm_obj.get("fallback_notice") or ""),
            "source_snapshot": normalized,
        }

        answer_text = (
            "### 对方行为模拟\\n"
            f"- 对方身份：`{opponent_role}` / {opponent_name}\\n"
            f"- 最可能动作：{opponent_action}\\n"
            f"- 风险变化：`{risk_delta}`\\n"
            f"- 我方下一步压力：{next_pressure}"
        )

        return {
            "workflow_key": WORKFLOW_KEY,
            "payload_json": json.dumps(payload, ensure_ascii=False),
            "opponent_action": opponent_action,
            "opponent_argument_json": json.dumps(opponent_argument, ensure_ascii=False),
            "opponent_evidence_json": json.dumps(opponent_evidence, ensure_ascii=False),
            "risk_delta": risk_delta,
            "next_pressure": next_pressure,
            "answer_text": answer_text,
            "degraded_flags_json": json.dumps(degraded_flags, ensure_ascii=False),
        }
    '''
).strip()


W04_NORMALIZE_CODE = dedent(
    '''
    import json


    def _first_not_empty(*values):
        for value in values:
            if value is None:
                continue
            if isinstance(value, str) and value.strip() == "":
                continue
            if isinstance(value, list) and len(value) == 0:
                continue
            return value
        return None


    def _to_list(value):
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return []
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
            return [s]
        return [str(value).strip()]


    def main(params: dict) -> dict:
        return {
            "current_stage": str(params.get("current_stage") or "report_ready"),
            "case_title": str(params.get("v_case_title") or "企鹅法庭模拟案件"),
            "case_summary": str(params.get("v_case_summary") or params.get("query") or "待补充案件摘要"),
            "focus_issues": _to_list(_first_not_empty(params.get("focus_issues_json"), params.get("focus_issues"), params.get("v_focus_issues"))),
            "claims": _to_list(_first_not_empty(params.get("claims_json"), params.get("claims"), params.get("v_claims"))),
            "missing_evidence": _to_list(_first_not_empty(params.get("missing_evidence_json"), params.get("missing_evidence"), params.get("v_missing_evidence"))),
            "opponent_arguments": _to_list(_first_not_empty(params.get("opponent_arguments_json"), params.get("opponent_arguments"), params.get("v_opponent_arguments"))),
            "legal_support_summary": str(params.get("legal_support_summary") or ""),
            "recommended_laws_json": str(params.get("recommended_laws_json") or ""),
            "recommended_cases_json": str(params.get("recommended_cases_json") or ""),
            "issue_mapping_json": str(params.get("issue_mapping_json") or ""),
            "opponent_role": str(params.get("opponent_role") or ""),
            "opponent_name": str(params.get("opponent_name") or ""),
            "notes": str(params.get("v_notes") or ""),
        }
    '''
).strip()


W04_SYSTEM_PROMPT = dedent(
    '''
    你是“企鹅法庭·沉浸式庭审模拟与立法沙盘推演”中的 W04_结果分析复盘 工作流。

    你会收到一个名为 normalized 的对象，内含案件摘要、争议焦点、诉求、证据缺口、对方观点等信息。

    你的任务是产出“本轮结果分析与复盘草案”，用于比赛展示和后续优化，不是正式法律意见。

    你必须只输出 JSON，不允许输出解释文字。

    固定 JSON 结构：
    {
      "win_rate_estimate": "0-100 之间的整数百分比字符串",
      "issue_assessment": [
        {"issue": "争点", "assessment": "当前判断"}
      ],
      "risk_points": ["风险点1", "风险点2"],
      "evidence_gaps": ["证据缺口1", "缺口2"],
      "next_steps": ["下一步建议1", "建议2"],
      "report_markdown": "面向用户展示的 markdown 复盘正文",
      "confidence": "low/medium/high",
      "fallback_notice": ""
    }

    约束：
    - win_rate_estimate 必须是字符串形式的整数，如 "62"。
    - issue_assessment、risk_points、evidence_gaps、next_steps 都要尽量具体。
    - report_markdown 需要像一个可直接展示的简洁复盘。
    - 信息不足时，也要给出保守、可执行的分析建议。
    '''
).strip()


W04_PACK_CODE = dedent(
    '''
    import json
    import re


    WORKFLOW_KEY = "outcome_analysis_report"
    VALID_CONFIDENCE = {"low", "medium", "high"}


    def _to_obj(value):
        if isinstance(value, dict):
            if "Output" in value and isinstance(value["Output"], dict):
                return value["Output"]
            return value
        if value is None:
            return {}
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return {}
            try:
                return json.loads(s)
            except Exception:
                return {}
        return {}


    def _parse_model_content(value):
        obj = _to_obj(value)
        content = obj.get("Content") if isinstance(obj, dict) else None
        if isinstance(content, dict):
            return content, False
        if isinstance(content, str):
            s = content.strip()
            if not s:
                return {}, True
            try:
                parsed = json.loads(s)
                if isinstance(parsed, dict):
                    return parsed, False
            except Exception:
                pass
        return {}, True


    def _list(value):
        return value if isinstance(value, list) else []


    def _sanitize_win_rate(value):
        text = str(value or "").strip()
        match = re.search(r"\\d+", text)
        if not match:
            return "50"
        number = max(0, min(100, int(match.group(0))))
        return str(number)


    def _sanitize_confidence(value):
        text = str(value or "").strip()
        return text if text in VALID_CONFIDENCE else "medium"


    def main(params: dict) -> dict:
        normalized = _to_obj(params.get("normalized"))
        llm_obj, parse_failed = _parse_model_content(params.get("draft"))

        degraded_flags = []
        if parse_failed:
            degraded_flags.append("llm_parse_failed")

        win_rate_estimate = _sanitize_win_rate(llm_obj.get("win_rate_estimate"))
        issue_assessment = _list(llm_obj.get("issue_assessment"))
        risk_points = _list(llm_obj.get("risk_points"))
        evidence_gaps = _list(llm_obj.get("evidence_gaps"))
        next_steps = _list(llm_obj.get("next_steps"))
        confidence = _sanitize_confidence(llm_obj.get("confidence"))
        report_markdown = str(llm_obj.get("report_markdown") or "").strip()
        if not report_markdown:
            report_markdown = (
                "### 结果分析复盘\\n"
                f"- 预估胜诉率：{win_rate_estimate}%\\n"
                f"- 置信度：{confidence}\\n"
                f"- 风险点：{'；'.join(str(x) for x in risk_points[:3]) if risk_points else '需继续核验争点与证据链'}"
            )
            degraded_flags.append("report_markdown_fallback")

        payload = {
            "workflow_key": WORKFLOW_KEY,
            "stage": str(normalized.get("current_stage") or "report_ready"),
            "win_rate_estimate": win_rate_estimate,
            "issue_assessment": issue_assessment,
            "risk_points": risk_points,
            "evidence_gaps": evidence_gaps,
            "next_steps": next_steps,
            "confidence": confidence,
            "report_markdown": report_markdown,
            "fallback_notice": str(llm_obj.get("fallback_notice") or ""),
            "source_snapshot": normalized,
        }
        answer_text = report_markdown

        return {
            "workflow_key": WORKFLOW_KEY,
            "payload_json": json.dumps(payload, ensure_ascii=False),
            "win_rate_estimate": win_rate_estimate,
            "issue_assessment_json": json.dumps(issue_assessment, ensure_ascii=False),
            "risk_points_json": json.dumps(risk_points, ensure_ascii=False),
            "evidence_gaps_json": json.dumps(evidence_gaps, ensure_ascii=False),
            "next_steps_json": json.dumps(next_steps, ensure_ascii=False),
            "report_markdown": report_markdown,
            "answer_text": answer_text,
            "degraded_flags_json": json.dumps(degraded_flags, ensure_ascii=False),
        }
    '''
).strip()


W00_NORMALIZE_CODE = dedent(
    '''
    import json


    VALID_STAGES = {
        "prepare",
        "investigation",
        "evidence",
        "debate",
        "final_statement",
        "mediation_or_judgment",
        "report_ready",
    }


    def _first_not_empty(*values):
        for value in values:
            if value is None:
                continue
            if isinstance(value, str) and value.strip() == "":
                continue
            if isinstance(value, list) and len(value) == 0:
                continue
            return value
        return None


    def _to_list(value):
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return []
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
            return [s]
        return [str(value).strip()]


    def _guess_stage(value):
        stage = str(value or "").strip()
        return stage if stage in VALID_STAGES else "prepare"


    def _stage_label(stage):
        mapping = {
            "prepare": "准备阶段",
            "investigation": "调查阶段",
            "evidence": "举证质证阶段",
            "debate": "法庭辩论阶段",
            "final_statement": "最后陈述阶段",
            "mediation_or_judgment": "调解或裁判阶段",
            "report_ready": "复盘报告阶段",
        }
        return mapping.get(stage, "庭审推进阶段")


    def _default_branch_focus(stage):
        mapping = {
            "prepare": "case_intake",
            "investigation": "fact_investigation",
            "evidence": "evidence_submission",
            "debate": "evidence_argumentation",
            "final_statement": "closing_statement",
            "mediation_or_judgment": "settlement_or_judgment",
            "report_ready": "report_generation",
        }
        return mapping.get(stage, "general")


    def main(params: dict) -> dict:
        stage = _guess_stage(_first_not_empty(params.get("current_stage"), params.get("stage")))
        raw_query = str(
            _first_not_empty(
                params.get("RewriteQuery"),
                params.get("rewritequery"),
                params.get("userquery"),
                params.get("query"),
                params.get("user_input"),
            )
            or ""
        )

        focus_issues = _to_list(_first_not_empty(params.get("focus_issues_json"), params.get("focus_issues"), params.get("v_focus_issues")))
        claims = _to_list(_first_not_empty(params.get("claims_json"), params.get("claims"), params.get("v_claims")))
        missing_evidence = _to_list(_first_not_empty(params.get("missing_evidence_json"), params.get("missing_evidence"), params.get("v_missing_evidence")))
        opponent_arguments = _to_list(_first_not_empty(params.get("opponent_arguments_json"), params.get("opponent_arguments"), params.get("v_opponent_arguments")))
        likely_arguments = _to_list(_first_not_empty(params.get("likely_arguments_json"), params.get("likely_arguments")))
        likely_evidence = _to_list(_first_not_empty(params.get("likely_evidence_json"), params.get("likely_evidence")))
        likely_strategies = _to_list(_first_not_empty(params.get("likely_strategies_json"), params.get("likely_strategies")))
        fact_keywords = _to_list(_first_not_empty(params.get("fact_keywords_json"), params.get("fact_keywords")))

        case_type = str(_first_not_empty(params.get("case_type"), params.get("v_case_type")) or "")
        case_title = str(params.get("v_case_title") or "企鹅法庭模拟案件")
        case_summary = str(params.get("v_case_summary") or raw_query or "待补充案件摘要")

        if not fact_keywords and raw_query:
            fact_keywords = [raw_query]

        return {
            "case_id": str(params.get("case_id") or ""),
            "simulation_id": str(params.get("simulation_id") or ""),
            "current_stage": stage,
            "stage_label": _stage_label(stage),
            "selected_action": str(params.get("selected_action") or "继续推进庭审"),
            "branch_focus": str(params.get("branch_focus") or _default_branch_focus(stage)),
            "case_type": case_type,
            "case_title": case_title,
            "case_summary": case_summary,
            "notes": str(params.get("v_notes") or ""),
            "focus_issues": focus_issues,
            "claims": claims,
            "missing_evidence": missing_evidence,
            "opponent_arguments": opponent_arguments,
            "likely_arguments": likely_arguments,
            "likely_evidence": likely_evidence,
            "likely_strategies": likely_strategies,
            "fact_keywords": fact_keywords,
            "opponent_role": str(params.get("opponent_role") or "defendant"),
            "opponent_name": str(params.get("opponent_name") or "对方当事人"),
            "raw_query": raw_query,
        }
    '''
).strip()


W00_SYSTEM_PROMPT = dedent(
    '''
    你是“企鹅法庭·沉浸式庭审模拟与立法沙盘推演”中的 W00_企鹅法庭主控编排 工作流。

    你会收到一个名为 normalized 的对象。你的任务是按当前阶段，把以下四个子能力的结果统一规划并合并成一个结构化 JSON：
    - 庭审场景生成
    - 法律支持检索
    - 对方行为模拟
    - 结果分析复盘

    注意：你现在输出的是“主控草案”，不是平台真实子工作流引用执行结果，但你的结构必须严格贴合主链设计。

    你必须只输出 JSON，不允许输出解释文字。

    固定 JSON 结构：
    {
      "stage_label": "阶段中文名",
      "route_plan": {
        "need_scene": true,
        "need_legal_support": true,
        "need_opponent": false,
        "need_analysis": false
      },
      "scene": {
        "scene_title": "",
        "scene_text": "",
        "speaker_role": "judge/plaintiff/defendant/agent/witness/other",
        "suggested_actions": [],
        "branch_focus": "",
        "next_stage_hint": ""
      },
      "legal_support": {
        "legal_support_summary": "",
        "recommended_laws": [],
        "recommended_cases": [],
        "issue_mapping": [],
        "missing_points": []
      },
      "opponent": {
        "opponent_action": "",
        "opponent_argument": [],
        "opponent_evidence": [],
        "risk_delta": "up/down/flat",
        "next_pressure": ""
      },
      "analysis": {
        "win_rate_estimate": "50",
        "issue_assessment": [],
        "risk_points": [],
        "evidence_gaps": [],
        "next_steps": [],
        "report_markdown": ""
      },
      "summary_markdown": "面向用户展示的本轮综合摘要"
    }

    路由规则必须遵守：
    - prepare / investigation / evidence：scene 和 legal_support 为主，opponent、analysis 可以保守简短
    - debate / final_statement：scene + legal_support + opponent 必须完整，analysis 可简洁
    - mediation_or_judgment / report_ready：scene + legal_support + analysis 必须完整，opponent 可作为增强输入

    约束：
    - 所有字段都必须存在，缺内容时返回空数组或空字符串，不要省略字段。
    - scene.suggested_actions 是“建议动作”，不是系统正式按钮。
    - 所有输出都必须体现“模拟、辅助、推演”定位。
    '''
).strip()


W00_PACK_CODE = dedent(
    '''
    import json
    import re


    WORKFLOW_KEY = "penguin_courtroom_master_orchestration"
    VALID_SCENE_ROLES = {"judge", "plaintiff", "defendant", "agent", "witness", "other"}
    VALID_RISK_DELTA = {"up", "down", "flat"}


    def _to_obj(value):
        if isinstance(value, dict):
            if "Output" in value and isinstance(value["Output"], dict):
                return value["Output"]
            return value
        if value is None:
            return {}
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return {}
            try:
                return json.loads(s)
            except Exception:
                return {}
        return {}


    def _parse_model_content(value):
        obj = _to_obj(value)
        content = obj.get("Content") if isinstance(obj, dict) else None
        if isinstance(content, dict):
            return content, False
        if isinstance(content, str):
            s = content.strip()
            if not s:
                return {}, True
            try:
                parsed = json.loads(s)
                if isinstance(parsed, dict):
                    return parsed, False
            except Exception:
                pass
        return {}, True


    def _sanitize_role(value):
        role = str(value or "").strip()
        return role if role in VALID_SCENE_ROLES else "judge"


    def _sanitize_risk(value):
        risk = str(value or "").strip()
        return risk if risk in VALID_RISK_DELTA else "flat"


    def _sanitize_win_rate(value):
        match = re.search(r"\\d+", str(value or ""))
        if not match:
            return "50"
        return str(max(0, min(100, int(match.group(0)))))


    def _default_route(stage):
        if stage in {"prepare", "investigation", "evidence"}:
            return {"need_scene": True, "need_legal_support": True, "need_opponent": False, "need_analysis": False}
        if stage in {"debate", "final_statement"}:
            return {"need_scene": True, "need_legal_support": True, "need_opponent": True, "need_analysis": False}
        return {"need_scene": True, "need_legal_support": True, "need_opponent": False, "need_analysis": True}


    def main(params: dict) -> dict:
        normalized = _to_obj(params.get("normalized"))
        llm_obj, parse_failed = _parse_model_content(params.get("draft"))

        degraded_flags = []
        if parse_failed:
            degraded_flags.append("llm_parse_failed")

        stage = str(normalized.get("current_stage") or "prepare")
        stage_label = str(llm_obj.get("stage_label") or normalized.get("stage_label") or "庭审推进阶段")
        route_plan = llm_obj.get("route_plan") if isinstance(llm_obj.get("route_plan"), dict) else _default_route(stage)

        scene = llm_obj.get("scene") if isinstance(llm_obj.get("scene"), dict) else {}
        legal_support = llm_obj.get("legal_support") if isinstance(llm_obj.get("legal_support"), dict) else {}
        opponent = llm_obj.get("opponent") if isinstance(llm_obj.get("opponent"), dict) else {}
        analysis = llm_obj.get("analysis") if isinstance(llm_obj.get("analysis"), dict) else {}

        if not scene:
            degraded_flags.append("scene_missing")
            scene = {
                "scene_title": f"{stage_label}主控推进",
                "scene_text": "当前信息不足，建议先补充案件摘要、争点和证据材料。",
                "speaker_role": "judge",
                "suggested_actions": [str(normalized.get("selected_action") or "继续推进庭审")],
                "branch_focus": str(normalized.get("branch_focus") or "general"),
                "next_stage_hint": stage,
            }
        scene["speaker_role"] = _sanitize_role(scene.get("speaker_role"))

        if not legal_support:
            degraded_flags.append("legal_support_missing")
            legal_support = {
                "legal_support_summary": "建议围绕案件要件事实、举证责任和抗辩方向继续检索法律支持。",
                "recommended_laws": [],
                "recommended_cases": [],
                "issue_mapping": [],
                "missing_points": [],
            }

        if not opponent:
            opponent = {
                "opponent_action": "",
                "opponent_argument": [],
                "opponent_evidence": [],
                "risk_delta": "flat",
                "next_pressure": "",
            }
        opponent["risk_delta"] = _sanitize_risk(opponent.get("risk_delta"))

        if not analysis:
            analysis = {
                "win_rate_estimate": "50",
                "issue_assessment": [],
                "risk_points": [],
                "evidence_gaps": [],
                "next_steps": [],
                "report_markdown": "",
            }
        analysis["win_rate_estimate"] = _sanitize_win_rate(analysis.get("win_rate_estimate"))

        payload = {
            "status": "ok",
            "workflow_key": WORKFLOW_KEY,
            "stage": stage,
            "stage_label": stage_label,
            "route_plan": route_plan,
            "scene": scene,
            "legal_support": legal_support,
            "opponent": opponent,
            "analysis": analysis,
            "source_snapshot": normalized,
            "degraded_flags": degraded_flags,
        }

        answer_text = str(llm_obj.get("summary_markdown") or "").strip()
        if not answer_text:
            answer_text = (
                f"### 企鹅法庭主控编排\\n"
                f"- 当前阶段：`{stage}`\\n"
                f"- 场景标题：{scene.get('scene_title') or '待补充'}\\n"
                f"- 法律支持摘要：{legal_support.get('legal_support_summary') or '待补充'}\\n"
                f"- 对方可能动作：{opponent.get('opponent_action') or '本阶段可暂不启用'}\\n"
                f"- 胜诉率预估：{analysis.get('win_rate_estimate') or '50'}%"
            )

        return {
            "workflow_key": WORKFLOW_KEY,
            "payload_json": json.dumps(payload, ensure_ascii=False),
            "stage": stage,
            "scene_title": str(scene.get("scene_title") or ""),
            "legal_support_summary": str(legal_support.get("legal_support_summary") or ""),
            "opponent_action": str(opponent.get("opponent_action") or ""),
            "win_rate_estimate": str(analysis.get("win_rate_estimate") or "50"),
            "scene_payload_json": json.dumps(scene, ensure_ascii=False),
            "legal_payload_json": json.dumps(legal_support, ensure_ascii=False),
            "opponent_payload_json": json.dumps(opponent, ensure_ascii=False),
            "analysis_payload_json": json.dumps(analysis, ensure_ascii=False),
            "answer_text": answer_text,
            "degraded_flags_json": json.dumps(degraded_flags, ensure_ascii=False),
        }
    '''
).strip()


WORKFLOW_SPECS = [
    {
        "name": "W00_企鹅法庭主控编排",
        "desc": "描述：主控编排工作流，按庭审阶段统一生成场景推进、法律支持、对方行为预判与结果复盘的综合输出。示例：民间借贷纠纷进入举证阶段如何推进？劳动争议到了辩论阶段如何预判对方动作并给出整体策略？",
        "normalize_name": "标准化输入",
        "normalize_desc": "兼容主链字段并统一当前庭审阶段语义",
        "normalize_code": W00_NORMALIZE_CODE,
        "llm_name": "主控编排推演",
        "llm_desc": "按阶段合并生成场景、法律支持、对方行为与结果分析草案",
        "system_prompt": W00_SYSTEM_PROMPT,
        "pack_name": "统一封装结果",
        "pack_desc": "将主控推演结果封装为可展示与可联调的结构化输出",
        "pack_code": W00_PACK_CODE,
        "end_fields": [
            ("workflow_key", "STRING", "主控工作流键"),
            ("payload_json", "STRING", "主控合并结果"),
            ("stage", "STRING", "当前阶段"),
            ("scene_title", "STRING", "场景标题"),
            ("legal_support_summary", "STRING", "法律支持摘要"),
            ("opponent_action", "STRING", "对方行为摘要"),
            ("win_rate_estimate", "STRING", "胜诉率估计"),
            ("scene_payload_json", "STRING", "场景子结果"),
            ("legal_payload_json", "STRING", "法律支持子结果"),
            ("opponent_payload_json", "STRING", "对方行为子结果"),
            ("analysis_payload_json", "STRING", "结果分析子结果"),
            ("degraded_flags_json", "STRING", "降级标记"),
        ],
        "examples": [
            "我是原告，民间借贷纠纷已经进入举证阶段，请直接给我本轮企鹅法庭综合推进结果。",
            "劳动争议案件到了辩论阶段，请输出主控编排结果，包含对方可能动作和整体风险判断。",
            "交通事故责任纠纷准备生成复盘报告，请给出主控工作流的综合输出。",
        ],
    },
    {
        "name": "W01_庭审场景生成",
        "desc": "描述：生成当前回合的庭审推进场景、主持提示、我方重点与建议动作。示例：举证阶段下一轮该怎么推进？调查阶段法官会先问什么？",
        "normalize_name": "输入标准化",
        "normalize_desc": "统一案件摘要、阶段信息、争议焦点和证据缺口",
        "normalize_code": W01_NORMALIZE_CODE,
        "llm_name": "庭审场景生成",
        "llm_desc": "生成本轮庭审叙事与推进建议",
        "system_prompt": W01_SYSTEM_PROMPT,
        "pack_name": "场景结果封装",
        "pack_desc": "封装场景推进结果，产出 workflow_key 与 payload_json",
        "pack_code": W01_PACK_CODE,
        "end_fields": [
            ("workflow_key", "STRING", "工作流键"),
            ("payload_json", "STRING", "场景结构化结果"),
            ("scene_title", "STRING", "场景标题"),
            ("scene_text", "STRING", "场景正文"),
            ("speaker_role", "STRING", "角色枚举"),
            ("suggested_actions_json", "STRING", "建议动作列表"),
            ("branch_focus", "STRING", "分支焦点"),
            ("next_stage_hint", "STRING", "下一阶段提示"),
            ("degraded_flags_json", "STRING", "降级标记"),
        ],
        "examples": [
            "我是原告，案件进入准备阶段，请生成本轮庭审场景和建议动作。",
            "请基于交通事故责任纠纷的举证质证阶段，生成下一轮法庭推进场景。",
        ],
    },
    {
        "name": "W02_法律支持检索",
        "desc": "描述：围绕当前争点输出法律支持摘要、推荐法源、参考案例与证据补强建议。示例：劳动争议中的加班工资举证责任应如何组织法律支持？",
        "normalize_name": "检索输入标准化",
        "normalize_desc": "统一争议焦点、诉求、证据缺口与事实关键词",
        "normalize_code": W02_NORMALIZE_CODE,
        "llm_name": "法律支持推演",
        "llm_desc": "生成法律支持摘要、法源建议和案例参考",
        "system_prompt": W02_SYSTEM_PROMPT,
        "pack_name": "法律支持封装",
        "pack_desc": "封装法律支持检索结果，产出 workflow_key 与 payload_json",
        "pack_code": W02_PACK_CODE,
        "end_fields": [
            ("workflow_key", "STRING", "工作流键"),
            ("payload_json", "STRING", "法律支持结构化结果"),
            ("legal_support_summary", "STRING", "法律支持摘要"),
            ("recommended_laws_json", "STRING", "推荐法源"),
            ("recommended_cases_json", "STRING", "推荐案例"),
            ("issue_mapping_json", "STRING", "争点映射"),
            ("missing_points_json", "STRING", "待补强问题"),
            ("degraded_flags_json", "STRING", "降级标记"),
        ],
        "examples": [
            "请围绕民间借贷纠纷中的借款合意和实际交付争点，输出法律支持检索结果。",
            "劳动争议案件进入辩论阶段，帮我整理法律支持摘要、法条方向和案例参考。",
        ],
    },
    {
        "name": "W03_对方行为模拟",
        "desc": "描述：模拟对方下一步最可能采取的动作、论点、证据与对我方造成的压力。示例：对方在辩论阶段可能如何抗辩？最后陈述前会如何收束主张？",
        "normalize_name": "对方信息标准化",
        "normalize_desc": "统一对方身份、既有论点、可能证据与当前阶段",
        "normalize_code": W03_NORMALIZE_CODE,
        "llm_name": "对方行为模拟",
        "llm_desc": "生成对方动作、论点和风险变化草案",
        "system_prompt": W03_SYSTEM_PROMPT,
        "pack_name": "对方行为封装",
        "pack_desc": "封装对方行为模拟结果，产出 workflow_key 与 payload_json",
        "pack_code": W03_PACK_CODE,
        "end_fields": [
            ("workflow_key", "STRING", "工作流键"),
            ("payload_json", "STRING", "对方行为结构化结果"),
            ("opponent_action", "STRING", "对方动作"),
            ("opponent_argument_json", "STRING", "对方论点"),
            ("opponent_evidence_json", "STRING", "对方证据"),
            ("risk_delta", "STRING", "风险变化"),
            ("next_pressure", "STRING", "下一步压力"),
            ("degraded_flags_json", "STRING", "降级标记"),
        ],
        "examples": [
            "请模拟被告在法庭辩论阶段最可能提出的抗辩动作和论点。",
            "交通事故责任纠纷进入最后陈述前，对方还可能怎样施压？",
        ],
    },
    {
        "name": "W04_结果分析复盘",
        "desc": "描述：输出本轮胜诉率估计、争点评估、风险点、证据缺口与复盘报告。示例：请基于当前回合给出复盘报告和下一步动作建议。",
        "normalize_name": "分析输入标准化",
        "normalize_desc": "统一分析所需的案件摘要、争点、证据缺口与对方观点",
        "normalize_code": W04_NORMALIZE_CODE,
        "llm_name": "结果分析复盘",
        "llm_desc": "生成胜诉率估计、风险点和复盘报告草案",
        "system_prompt": W04_SYSTEM_PROMPT,
        "pack_name": "复盘结果封装",
        "pack_desc": "封装结果分析复盘，产出 workflow_key 与 payload_json",
        "pack_code": W04_PACK_CODE,
        "end_fields": [
            ("workflow_key", "STRING", "工作流键"),
            ("payload_json", "STRING", "分析结构化结果"),
            ("win_rate_estimate", "STRING", "胜诉率估计"),
            ("issue_assessment_json", "STRING", "争点评估"),
            ("risk_points_json", "STRING", "风险点"),
            ("evidence_gaps_json", "STRING", "证据缺口"),
            ("next_steps_json", "STRING", "下一步建议"),
            ("report_markdown", "STRING", "复盘报告"),
            ("degraded_flags_json", "STRING", "降级标记"),
        ],
        "examples": [
            "请对当前民间借贷纠纷回合输出结果分析复盘和胜诉率估计。",
            "劳动争议案件准备进入报告阶段，请生成风险点、证据缺口和下一步建议。",
        ],
    },
]


def stable_id(*parts: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "penguin-yuanqi::" + "::".join(parts)))


def now_ms() -> str:
    return str(int(time.time() * 1000))


def load_base_templates() -> dict[str, dict]:
    base = json.loads(BASE_WORKFLOW_PATH.read_text(encoding="utf-8"))
    nodes = base["Nodes"]
    code_nodes = [copy.deepcopy(node) for node in nodes if node["NodeType"] == "CODE_EXECUTOR"]

    def by_name(name: str) -> dict | None:
        for node in nodes:
            if node["NodeName"] == name:
                return copy.deepcopy(node)
        return None

    def by_type(node_type: str) -> dict:
        for node in nodes:
            if node["NodeType"] == node_type:
                return copy.deepcopy(node)
        raise ValueError(f"missing node template: {node_type}")

    return {
        "start": by_type("START"),
        "code1": by_name("标准化输入") or code_nodes[0],
        "llm": by_type("LLM"),
        "code2": by_name("统一封装结果") or (code_nodes[1] if len(code_nodes) > 1 else code_nodes[0]),
        "answer": by_type("ANSWER"),
        "end": by_type("END"),
    }


def make_ref_input(name: str, input_type: str, node_id: str, json_path: str, desc: str = "") -> dict:
    return {
        "Name": name,
        "Type": input_type,
        "Input": {"InputType": "REFERENCE_OUTPUT", "Reference": {"NodeID": node_id, "JsonPath": json_path}},
        "Desc": desc,
        "IsRequired": False,
        "SubInputs": [],
        "DefaultValue": "",
        "DefaultFileName": "",
    }


def make_custom_var_input(name: str, input_type: str, custom_var_id: str, desc: str = "") -> dict:
    return {
        "Name": name,
        "Type": input_type,
        "Input": {"InputType": "CUSTOM_VARIABLE", "CustomVarID": custom_var_id},
        "Desc": desc,
        "IsRequired": False,
        "SubInputs": [],
        "DefaultValue": "",
        "DefaultFileName": "",
    }


def make_output_property(title: str, output_type: str, desc: str = "") -> dict:
    return {"Title": title, "Type": output_type, "Required": [], "Properties": [], "Desc": desc, "AnalysisMethod": "COVER"}


def make_object_output(title: str, properties: list[dict], desc: str = "输出内容") -> dict:
    return {"Title": title, "Type": "OBJECT", "Required": [], "Properties": properties, "Desc": desc, "AnalysisMethod": "COVER"}


def make_nodeui_output(title: str, output_type: str, desc: str = "输出内容") -> dict:
    return {"label": title, "desc": desc, "optionType": "REFERENCE_OUTPUT", "type": output_type, "children": []}


DEFAULT_LLM_PROMPT = "请基于输入变量与系统提示，严格输出符合要求的 JSON。"
DEFAULT_ANSWER_TEXT = "已生成结构化结果，请查看结束节点输出。"


def workflow_code(name: str) -> str:
    return str(name or "").split("_", 1)[0]


def get_start_param_specs(spec: dict) -> list[tuple[str, str, str]]:
    return START_PARAM_SPECS.get(workflow_code(spec["name"]), [])


def make_start_workflow_param(name: str, desc: str, default_value: str = "") -> dict:
    return {
        "Name": name,
        "Type": DEFAULT_STRING_TYPE,
        "Desc": desc,
        "IsRequired": False,
        "SubInputs": [],
        "DefaultValue": default_value,
        "DefaultFileName": "",
    }


def build_start_workflow_params(spec: dict) -> list[dict]:
    return [make_start_workflow_param(name, desc, example) for name, desc, example in get_start_param_specs(spec)]


def extract_main_return_keys(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "main":
            continue
        for child in ast.walk(node):
            if not isinstance(child, ast.Return) or not isinstance(child.value, ast.Dict):
                continue
            keys: list[str] = []
            for key in child.value.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    keys.append(key.value)
                elif isinstance(key, ast.Str):
                    keys.append(key.s)
            if keys:
                return keys
    return []


def guess_property_type(field_name: str) -> str:
    if field_name in OBJECT_LIKE_NORMALIZE_FIELDS or field_name.endswith("_json"):
        return "OBJECT"
    return "STRING"


def build_normalize_inputs(spec: dict) -> list[dict]:
    inputs: list[dict] = []
    seen: set[str] = set()

    for name, desc, _ in get_start_param_specs(spec):
        inputs.append(make_custom_var_input(name, DEFAULT_STRING_TYPE, f"API.{name}", desc))
        seen.add(name)

    for alias in SYSTEM_QUERY_ALIASES:
        if alias in seen:
            continue
        inputs.append(make_custom_var_input(alias, DEFAULT_STRING_TYPE, "SYS.RewriteQuery", "system query"))
        seen.add(alias)

    return inputs


def build_normalize_output_properties(spec: dict) -> list[dict]:
    return [
        make_output_property(field_name, guess_property_type(field_name), field_name)
        for field_name in extract_main_return_keys(spec["normalize_code"])
    ]


def build_param_rows(workflow_id: str, start_node_id: str, start_node_name: str, spec: dict) -> list[list[str]]:
    rows: list[list[str]] = []
    for name, desc, example in get_start_param_specs(spec):
        rows.append(
            [
                workflow_id,
                start_node_id,
                start_node_name,
                stable_id(workflow_id, "param", name),
                name,
                desc,
                DEFAULT_STRING_TYPE,
                example,
                "",
                "",
            ]
        )
    return rows


def build_variable_rows(workflow_id: str, spec: dict) -> list[list[str]]:
    rows: list[list[str]] = []
    for name, desc, _ in get_start_param_specs(spec):
        rows.append(
            [
                workflow_id,
                stable_id(workflow_id, "var", name),
                name,
                desc,
                DEFAULT_STRING_TYPE,
                "",
                "",
                DEFAULT_START_PARAM_KIND,
            ]
        )
    return rows


def patch_node_ui(
    node: dict,
    node_id: str,
    *,
    x: int,
    y: int,
    source: bool,
    target: bool,
    output: list[dict] | None = None,
    content: str | None = None,
    display_prompt: str | None = None,
    system_prompt: str | None = None,
) -> None:
    ui = json.loads(node["NodeUI"])
    ui["position"]["x"] = x
    ui["position"]["y"] = y
    ui["data"]["source"] = source
    ui["data"]["target"] = target
    if output is not None:
        ui["data"]["output"] = output
    if content is not None:
        ui["data"]["content"] = content
    if display_prompt is not None:
        ui["data"]["displayPrompt"] = display_prompt
    if system_prompt is not None:
        ui["data"]["systemPrompt"] = system_prompt
    connected_handles: dict[str, bool] = {}
    if source:
        connected_handles[f"{node_id}-source"] = True
    if target:
        connected_handles[f"{node_id}-target"] = True
    ui["data"]["connectedHandles"] = connected_handles
    node["NodeUI"] = json.dumps(ui, ensure_ascii=False, separators=(",", ":"))


def make_edge(source_id: str, target_id: str) -> dict:
    source_handle = f"{source_id}-source"
    target_handle = f"{target_id}-target"
    return {
        "source": source_id,
        "sourceHandle": source_handle,
        "target": target_id,
        "targetHandle": target_handle,
        "type": "custom",
        "data": {"connectedNodeIsHovering": False, "error": False, "isHovering": False},
        "id": f"xy-edge__{source_id}{source_handle}-{target_id}{target_handle}",
        "selected": False,
        "animated": False,
    }


def build_workflow(spec: dict, templates: dict[str, dict]) -> dict:
    workflow_id = stable_id("workflow", spec["name"])
    release_time = now_ms()

    start_id = stable_id(workflow_id, "start")
    code1_id = stable_id(workflow_id, "code1")
    llm_id = stable_id(workflow_id, "llm")
    code2_id = stable_id(workflow_id, "code2")
    answer_id = stable_id(workflow_id, "answer")
    end_id = stable_id(workflow_id, "end")

    start = copy.deepcopy(templates["start"])
    start["NodeID"] = start_id
    start["NodeName"] = "开始"
    start["NodeDesc"] = ""
    start["StartNodeData"] = {"WorkflowParams": build_start_workflow_params(spec)}
    start["Inputs"] = []
    start["Outputs"] = []
    start["NextNodeIDs"] = [code1_id]
    patch_node_ui(start, start_id, x=220, y=260, source=True, target=False, output=[])

    normalize_properties = build_normalize_output_properties(spec)

    code1 = copy.deepcopy(templates["code1"])
    code1["NodeID"] = code1_id
    code1["NodeName"] = spec["normalize_name"]
    code1["NodeDesc"] = spec["normalize_desc"]
    code1["CodeExecutorNodeData"]["Code"] = spec["normalize_code"]
    code1["Inputs"] = build_normalize_inputs(spec)
    code1["Outputs"] = [make_object_output("Output", [], "标准化输入对象")]
    code1["Outputs"] = [make_object_output("Output", normalize_properties, "normalized input object")]
    code1["NextNodeIDs"] = [llm_id]
    patch_node_ui(code1, code1_id, x=560, y=260, source=True, target=True, output=[make_nodeui_output("Output", "OBJECT", "标准化输入对象")], content=spec["normalize_name"])

    llm = copy.deepcopy(templates["llm"])
    llm["NodeID"] = llm_id
    llm["NodeName"] = spec["llm_name"]
    llm["NodeDesc"] = spec["llm_desc"]
    llm["LLMNodeData"]["SystemPrompt"] = spec["system_prompt"]
    llm["LLMNodeData"]["Prompt"] = DEFAULT_LLM_PROMPT
    llm["Inputs"] = [make_ref_input("normalized", "OBJECT", code1_id, "Output", "标准化输入")]
    llm["Inputs"] = [make_ref_input("normalized", "OBJECT", code1_id, "Output", "normalized input")]
    llm["NextNodeIDs"] = [code2_id]
    patch_node_ui(
        llm,
        llm_id,
        x=920,
        y=260,
        source=True,
        target=True,
        output=json.loads(templates["llm"]["NodeUI"])["data"].get("output", []),
        content=spec["llm_name"],
        display_prompt=DEFAULT_LLM_PROMPT,
        system_prompt=spec["system_prompt"],
    )

    code2_properties = []
    for field_name, field_type, field_desc in spec["end_fields"]:
        code2_properties.append(make_output_property(field_name, field_type, field_desc))
    code2_properties.append(make_output_property("answer_text", "STRING", "reply text"))

    code2 = copy.deepcopy(templates["code2"])
    code2["NodeID"] = code2_id
    code2["NodeName"] = spec["pack_name"]
    code2["NodeDesc"] = spec["pack_desc"]
    code2["CodeExecutorNodeData"]["Code"] = spec["pack_code"]
    code2["Inputs"] = [make_ref_input("normalized", "OBJECT", code1_id, "Output", "标准化输入"), make_ref_input("draft", "OBJECT", llm_id, "Output", "模型草案")]
    code2["Outputs"] = [make_object_output("Output", code2_properties, "封装结果")]
    code2["Inputs"] = [
        make_ref_input("normalized", "OBJECT", code1_id, "Output", "normalized input"),
        make_ref_input("draft", "OBJECT", llm_id, "Output", "model draft"),
    ]
    code2["Outputs"] = [make_object_output("Output", code2_properties, "packaged output")]
    code2["NextNodeIDs"] = [answer_id]
    patch_node_ui(code2, code2_id, x=1280, y=260, source=True, target=True, output=[make_nodeui_output("Output", "OBJECT", "封装结果")], content=spec["pack_name"])

    answer = copy.deepcopy(templates["answer"])
    answer["NodeID"] = answer_id
    answer["NodeName"] = "回复用户"
    answer["NodeDesc"] = "向用户展示本工作流的结果摘要"
    answer["AnswerNodeData"]["Answer"] = "{{answer_text}}"
    answer["Inputs"] = [make_ref_input("answer_text", "STRING", code2_id, "Output.answer_text", "reply text")]
    answer["Outputs"] = copy.deepcopy(templates["answer"]["Outputs"])
    answer["NextNodeIDs"] = [end_id]
    patch_node_ui(answer, answer_id, x=1640, y=220, source=True, target=True, output=json.loads(templates["answer"]["NodeUI"])["data"].get("output", []), content="回复用户")

    end = copy.deepcopy(templates["end"])
    end["NodeID"] = end_id
    end["NodeName"] = "结束"
    end["NodeDesc"] = "结束并对外暴露结构化结果"
    end["Inputs"] = [make_ref_input(name, field_type, code2_id, f"Output.{name}", desc) for name, field_type, desc in spec["end_fields"]]
    end["Outputs"] = [make_output_property(name, field_type, desc) for name, field_type, desc in spec["end_fields"]]
    end["NextNodeIDs"] = []
    patch_node_ui(end, end_id, x=1640, y=360, source=False, target=True, output=[])

    return {
        "ProtoVersion": "V2_6",
        "WorkflowID": workflow_id,
        "WorkflowName": spec["name"],
        "WorkflowDesc": spec["desc"],
        "Nodes": [start, code1, llm, code2, answer, end],
        "Edge": json.dumps([make_edge(start_id, code1_id), make_edge(code1_id, llm_id), make_edge(llm_id, code2_id), make_edge(code2_id, answer_id), make_edge(answer_id, end_id)], ensure_ascii=False, separators=(",", ":")),
        "Mode": "NORMAL",
        "ReleaseTime": release_time,
        "UpdateTime": release_time,
    }


def column_name(index: int) -> str:
    result = ""
    while index > 0:
        index, rem = divmod(index - 1, 26)
        result = chr(65 + rem) + result
    return result


def build_shared_strings(rows: list[list[str]]) -> tuple[str, list[list[int]]]:
    mapping: dict[str, int] = {}
    strings: list[str] = []
    row_indexes: list[list[int]] = []
    for row in rows:
        current_row = []
        for value in row:
            text = "" if value is None else str(value)
            if text not in mapping:
                mapping[text] = len(strings)
                strings.append(text)
            current_row.append(mapping[text])
        row_indexes.append(current_row)
    xml = '<?xml version="1.0" encoding="UTF-8"?>' + f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(strings)}" uniqueCount="{len(strings)}">' + "".join(f"<si><t>{escape(value)}</t></si>" for value in strings) + "</sst>"
    return xml, row_indexes


def build_sheet_xml(rows: list[list[str]], row_indexes: list[list[int]]) -> str:
    last_col = column_name(len(rows[0]))
    last_row = len(rows)
    body = []
    for row_num, index_row in enumerate(row_indexes, start=1):
        cells = []
        for col_num, shared_idx in enumerate(index_row, start=1):
            cells.append(f'<c r="{column_name(col_num)}{row_num}" t="s"><v>{shared_idx}</v></c>')
        body.append(f'<row r="{row_num}">{"".join(cells)}</row>')
    return '<?xml version="1.0" encoding="UTF-8"?>' + '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">' + f'<dimension ref="A1:{last_col}{last_row}"></dimension>' + '<sheetViews><sheetView tabSelected="true" workbookViewId="0"></sheetView></sheetViews><sheetFormatPr defaultRowHeight="15"></sheetFormatPr>' + f'<sheetData>{"".join(body)}</sheetData></worksheet>'


def rewrite_xlsx(template_name: str, output_path: Path, rows: list[list[str]]) -> None:
    template_path = BASE_PACKAGE_DIR / template_name
    shared_strings_xml, row_indexes = build_shared_strings(rows)
    sheet_xml = build_sheet_xml(rows, row_indexes)
    with zipfile.ZipFile(template_path, "r") as zin, zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "xl/sharedStrings.xml":
                data = shared_strings_xml.encode("utf-8")
            elif item.filename == "xl/worksheets/sheet1.xml":
                data = sheet_xml.encode("utf-8")
            zout.writestr(item, data)


def safe_remove(path: Path) -> None:
    resolved = path.resolve()
    exports_root = EXPORTS_DIR.resolve()
    if exports_root not in resolved.parents and resolved != exports_root:
        raise ValueError(f"refusing to delete path outside exports: {resolved}")
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def zip_directory(directory: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(directory.rglob("*")):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(directory))


def write_package(output_dir: Path, workflows: list[dict]) -> None:
    if output_dir.exists():
        safe_remove(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    workflow_rows = [["工作流ID", "工作流名称", "工作流描述", "画布结构"]]
    param_rows = [["工作流ID", "工作流节点ID", "工作流节点名称", "参数ID", "参数名称", "参数描述", "参数类型", "参数正确示例", "参数错误示例", "父参数ID"]]
    # 元器真实导出样例里「变量.xlsx」为空表头；导入校验也会把自造的 START 枚举
    # 标成“变量模块类型错误”。这里保留表头结构，但不再自动写变量行。
    variable_rows = [["工作流ID", "变量ID", "变量名称", "变量描述", "变量类型", "变量默认值", "变量默认值文件名称", "参数类型"]]
    example_rows = [["工作流ID", "示例问法ID", "示例问法内容"]]
    for workflow, spec in zip(workflows, WORKFLOW_SPECS):
        filename = f"{workflow['WorkflowID']}_workflow.json"
        (output_dir / filename).write_text(json.dumps(workflow, ensure_ascii=True, separators=(",", ":")), encoding="utf-8")
        workflow_rows.append([workflow["WorkflowID"], workflow["WorkflowName"], workflow["WorkflowDesc"], filename])
        start_node = next(node for node in workflow["Nodes"] if node["NodeType"] == "START")
        param_rows.extend(build_param_rows(workflow["WorkflowID"], start_node["NodeID"], start_node["NodeName"], spec))
        for idx, example in enumerate(spec["examples"], start=1):
            example_rows.append([workflow["WorkflowID"], stable_id(workflow["WorkflowID"], "example", str(idx)), example])
    rewrite_xlsx("工作流程.xlsx", output_dir / "工作流程.xlsx", workflow_rows)
    rewrite_xlsx("工作流程引用.xlsx", output_dir / "工作流程引用.xlsx", [["工作流ID", "工作流节点ID", "工作流引用ID", "工作流引用名称"]])
    rewrite_xlsx("参数.xlsx", output_dir / "参数.xlsx", param_rows)
    rewrite_xlsx("变量.xlsx", output_dir / "变量.xlsx", variable_rows)
    rewrite_xlsx("示例问法.xlsx", output_dir / "示例问法.xlsx", example_rows)


def validate_package(output_dir: Path, workflows: list[dict]) -> dict:
    results = {"workflow_count": 0, "workflows_xlsx_exists": (output_dir / "工作流程.xlsx").exists(), "examples_xlsx_exists": (output_dir / "示例问法.xlsx").exists()}
    for workflow in workflows:
        path = output_dir / f"{workflow['WorkflowID']}_workflow.json"
        loaded = json.loads(path.read_text(encoding="utf-8"))
        json.loads(loaded["Edge"])
        results["workflow_count"] += 1
    return results


def main() -> None:
    templates = load_base_templates()
    workflows = [build_workflow(spec, templates) for spec in WORKFLOW_SPECS]
    for target in [FORMAL_ZIP, ASCII_DIR, ASCII_ZIP]:
        if target.exists():
            safe_remove(target)
    write_package(FORMAL_DIR, workflows)
    zip_directory(FORMAL_DIR, FORMAL_ZIP)
    shutil.copytree(FORMAL_DIR, ASCII_DIR)
    zip_directory(ASCII_DIR, ASCII_ZIP)
    print(json.dumps({"formal_dir": str(FORMAL_DIR), "formal_zip": str(FORMAL_ZIP), "ascii_dir": str(ASCII_DIR), "ascii_zip": str(ASCII_ZIP), "validation": validate_package(FORMAL_DIR, workflows), "workflow_names": [workflow["WorkflowName"] for workflow in workflows]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
