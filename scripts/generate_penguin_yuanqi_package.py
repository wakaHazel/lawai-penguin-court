import copy
import json
import shutil
import time
import uuid
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(r"E:\lawai")
SAMPLE_DIR = ROOT / "data" / "yuanqi-sample"
OUTPUT_DIR = ROOT / "exports" / "企鹅法庭元器导入包_v1"


def load_sample_workflow() -> dict:
    return json.loads((SAMPLE_DIR / "sample_workflow.json").read_text(encoding="utf-8"))


def find_sample_node(sample: dict, node_type: str, *, node_name: str | None = None) -> dict:
    for node in sample["Nodes"]:
        if node["NodeType"] != node_type:
            continue
        if node_name is not None and node["NodeName"] != node_name:
            continue
        return copy.deepcopy(node)
    raise ValueError(f"sample node not found: {node_type} {node_name or ''}")


def new_id() -> str:
    return str(uuid.uuid4())


def now_ms() -> str:
    return str(int(time.time() * 1000))


def make_ref_input(name: str, input_type: str, node_id: str, json_path: str, desc: str = "") -> dict:
    return {
        "Name": name,
        "Type": input_type,
        "Input": {
            "InputType": "REFERENCE_OUTPUT",
            "Reference": {
                "NodeID": node_id,
                "JsonPath": json_path,
            },
        },
        "Desc": desc,
        "IsRequired": False,
        "SubInputs": [],
        "DefaultValue": "",
        "DefaultFileName": "",
    }


def make_output_property(title: str, output_type: str, desc: str = "") -> dict:
    return {
        "Title": title,
        "Type": output_type,
        "Required": [],
        "Properties": [],
        "Desc": desc,
        "AnalysisMethod": "COVER",
    }


def make_object_output(title: str, properties: list[dict], desc: str = "输出内容") -> dict:
    return {
        "Title": title,
        "Type": "OBJECT",
        "Required": [],
        "Properties": properties,
        "Desc": desc,
        "AnalysisMethod": "COVER",
    }


def make_nodeui_output(title: str, output_type: str, desc: str = "输出内容", *, children: list[dict] | None = None) -> dict:
    return {
        "label": title,
        "desc": desc,
        "optionType": "REFERENCE_OUTPUT",
        "type": output_type,
        "children": children or [],
    }


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
    measured_width: int | None = None,
    measured_height: int | None = None,
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
    connected_handles: dict[str, bool] = {}
    if source:
        connected_handles[f"{node_id}-source"] = True
    if target:
        connected_handles[f"{node_id}-target"] = True
    ui["data"]["connectedHandles"] = connected_handles
    if measured_width is not None:
        ui["measured"]["width"] = measured_width
    if measured_height is not None:
        ui["measured"]["height"] = measured_height
    node["NodeUI"] = json.dumps(ui, ensure_ascii=False, separators=(",", ":"))


def make_edge(source_id: str, target_id: str, *, source_handle: str | None = None, target_handle: str | None = None) -> dict:
    source_handle = source_handle or f"{source_id}-source"
    target_handle = target_handle or f"{target_id}-target"
    return {
        "source": source_id,
        "sourceHandle": source_handle,
        "target": target_id,
        "targetHandle": target_handle,
        "type": "custom",
        "data": {
            "connectedNodeIsHovering": False,
            "error": False,
            "isHovering": False,
        },
        "id": f"xy-edge__{source_id}{source_handle}-{target_id}{target_handle}",
        "selected": False,
        "animated": False,
    }


NORMALIZE_CODE = """\
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


def _guess_stage(stage):
    stage = str(stage or "").strip()
    return stage if stage in VALID_STAGES else "prepare"


def _default_action(stage):
    mapping = {
        "prepare": "梳理案情与诉请",
        "investigation": "补充事实调查",
        "evidence": "提交并质证证据",
        "debate": "围绕争点展开辩论",
        "final_statement": "提交最后陈述",
        "mediation_or_judgment": "进入调解或等待裁判",
        "report_ready": "输出复盘报告",
    }
    return mapping.get(stage, "继续推进庭审")


def _default_focus(stage):
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


def _to_json_str(items):
    return json.dumps(items, ensure_ascii=False)


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

    focus_issues = _to_list(_first_not_empty(params.get("focus_issues"), params.get("v_focus_issues")))
    claims = _to_list(_first_not_empty(params.get("claims"), params.get("v_claims")))
    missing_evidence = _to_list(_first_not_empty(params.get("missing_evidence"), params.get("v_missing_evidence")))
    opponent_arguments = _to_list(_first_not_empty(params.get("opponent_arguments"), params.get("v_opponent_arguments")))
    likely_arguments = _to_list(params.get("likely_arguments"))
    likely_evidence = _to_list(params.get("likely_evidence"))
    likely_strategies = _to_list(params.get("likely_strategies"))
    fact_keywords = _to_list(params.get("fact_keywords"))

    case_type = str(_first_not_empty(params.get("case_type"), params.get("v_case_type")) or "")
    case_title = str(params.get("v_case_title") or "")
    case_summary = str(params.get("v_case_summary") or raw_query or "")

    if not case_title:
        case_title = "企鹅法庭模拟案件"

    if not fact_keywords and raw_query:
        fact_keywords = [raw_query]

    return {
        "case_id": str(params.get("case_id") or ""),
        "simulation_id": str(params.get("simulation_id") or ""),
        "raw_query": raw_query,
        "current_stage": stage,
        "turn_index": int(params.get("turn_index") or 1),
        "selected_action": str(params.get("selected_action") or _default_action(stage)),
        "next_stage": str(params.get("next_stage") or stage),
        "branch_focus": str(params.get("branch_focus") or _default_focus(stage)),
        "case_type": case_type,
        "v_case_type": str(params.get("v_case_type") or case_type),
        "v_case_title": case_title,
        "v_case_summary": case_summary,
        "v_notes": str(params.get("v_notes") or ""),
        "focus_issues_json": _to_json_str(focus_issues),
        "claims_json": _to_json_str(claims),
        "missing_evidence_json": _to_json_str(missing_evidence),
        "fact_keywords_json": _to_json_str(fact_keywords),
        "opponent_arguments_json": _to_json_str(opponent_arguments),
        "likely_arguments_json": _to_json_str(likely_arguments),
        "likely_evidence_json": _to_json_str(likely_evidence),
        "likely_strategies_json": _to_json_str(likely_strategies),
        "opponent_role": str(params.get("opponent_role") or "other"),
        "opponent_name": str(params.get("opponent_name") or "对方当事人"),
    }
"""


LLM_SYSTEM_PROMPT = """你是“企鹅法庭·沉浸式庭审模拟与立法沙盘推演”工作流中的主控推演引擎。

你会收到一个名为 normalized 的输入对象，包含案件摘要、庭审阶段、争点、主张、证据缺口、对方可能观点等。

你的任务不是做泛泛法律科普，而是生成一份可被后续代码节点消费的严格 JSON，用于：
1. 庭审场景推进
2. 对方行为模拟
3. 胜诉率与风险分析
4. 生成给用户展示的 markdown 文本

请严格遵守：
- 只输出 JSON，不要输出任何解释。
- 所有字段都必须存在。
- 没有内容时返回空字符串、空数组或空对象，不要省略字段。
- 不能声称替代正式法律意见，要体现“模拟、辅助、建议”的定位。

输出 JSON 结构固定为：
{
  "stage_label": "阶段中文名",
  "courtroom_script": {
    "judge_opening": "法官或主持人开场推进语",
    "user_side_focus": ["我方本轮应重点强调的点1", "点2"],
    "evidence_focus": ["本轮关键证据点1", "点2"],
    "hearing_points": ["本轮庭审推进点1", "点2", "点3"],
    "next_action_suggestion": "下一步建议动作"
  },
  "opponent": {
    "likely_move": "对方本轮最可能动作",
    "likely_argument": ["对方可能论点1", "论点2"],
    "likely_evidence": ["对方可能证据1", "证据2"],
    "rebuttal_points": ["我方应对要点1", "要点2"]
  },
  "analysis": {
    "win_rate_estimate": "0-100 的整数百分比字符串",
    "confidence": "low/medium/high",
    "risk_points": ["风险点1", "风险点2"],
    "evidence_gaps": ["证据缺口1", "缺口2"],
    "next_stage": "下一阶段英文枚举"
  },
  "answer_markdown": "面向用户展示的 markdown，总结当前阶段、下一步、对方可能动作、风险与建议"
}

阶段规则：
- prepare / investigation / evidence：analysis 可以较简短，但也要有字段；opponent 允许提供预判。
- debate / final_statement：必须强化 opponent 与 rebuttal_points。
- mediation_or_judgment / report_ready：必须强化 analysis、win_rate_estimate、risk_points、evidence_gaps。

如果输入信息不足，也必须基于已有信息给出保守、明确、结构化的模拟结果。"""


PACK_CODE = """\
import json


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
    if isinstance(obj, dict) and all(k in obj for k in ("courtroom_script", "opponent", "analysis")):
        return obj, False
    return {}, True


def _to_list(value):
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return []


def main(params: dict) -> dict:
    normalized = _to_obj(params.get("normalized"))
    llm_obj, parse_failed = _parse_model_content(params.get("draft"))

    stage = str(normalized.get("current_stage") or "prepare")
    case_id = str(normalized.get("case_id") or "")
    stage_label = str(llm_obj.get("stage_label") or stage)
    courtroom_script = llm_obj.get("courtroom_script") if isinstance(llm_obj.get("courtroom_script"), dict) else {}
    opponent = llm_obj.get("opponent") if isinstance(llm_obj.get("opponent"), dict) else {}
    analysis = llm_obj.get("analysis") if isinstance(llm_obj.get("analysis"), dict) else {}

    degraded_flags = []
    if parse_failed:
        degraded_flags.append("llm_parse_failed")
    if not courtroom_script:
        degraded_flags.append("scene_missing")
        courtroom_script = {
            "judge_opening": "当前信息不足，建议先补充案情摘要、争点和证据材料。",
            "user_side_focus": [],
            "evidence_focus": [],
            "hearing_points": [],
            "next_action_suggestion": "补充事实与证据后重新推演。"
        }

    result = {
        "status": "ok",
        "workflow_key": "penguin_courtroom_monolith",
        "case_id": case_id,
        "stage": stage,
        "stage_label": stage_label,
        "scene": courtroom_script,
        "opponent": opponent,
        "analysis": analysis,
        "degraded_flags": degraded_flags,
        "source_snapshot": normalized,
    }

    answer_markdown = str(llm_obj.get("answer_markdown") or "").strip()
    if not answer_markdown:
        answer_markdown = (
            f"### 企鹅法庭·{stage_label}\\n"
            f"- 当前阶段：`{stage}`\\n"
            f"- 建议动作：{courtroom_script.get('next_action_suggestion') or '继续补充信息并推进'}\\n"
            f"- 降级标记：{', '.join(degraded_flags) if degraded_flags else '无'}"
        )

    return {
        "answer_text": answer_markdown,
        "result_json": json.dumps(result, ensure_ascii=False),
        "stage": stage,
        "case_id": case_id,
        "degraded_flags_json": json.dumps(degraded_flags, ensure_ascii=False),
    }
"""


def build_workflow() -> tuple[dict, str]:
    sample = load_sample_workflow()
    workflow_id = new_id()
    json_name = f"{workflow_id}_workflow.json"

    start_id = new_id()
    normalize_id = new_id()
    llm_id = new_id()
    pack_id = new_id()
    reply_id = new_id()
    end_id = new_id()

    start = find_sample_node(sample, "START")
    start["NodeID"] = start_id
    start["NodeName"] = "开始"
    start["NodeDesc"] = ""
    start["StartNodeData"] = {"WorkflowParams": []}
    start["Inputs"] = []
    start["Outputs"] = []
    start["NextNodeIDs"] = [normalize_id]
    patch_node_ui(start, start_id, x=220, y=260, source=True, target=False, output=[], measured_height=88)

    normalize = find_sample_node(sample, "CODE_EXECUTOR")
    normalize["NodeID"] = normalize_id
    normalize["NodeName"] = "标准化输入"
    normalize["NodeDesc"] = "兼容企鹅法庭桥接字段与自由问句输入"
    normalize["CodeExecutorNodeData"] = {"Code": NORMALIZE_CODE, "Language": "PYTHON3"}
    normalize["Inputs"] = []
    normalize["Outputs"] = [
        make_object_output(
            "Output",
            [
                make_output_property("case_id", "STRING"),
                make_output_property("simulation_id", "STRING"),
                make_output_property("raw_query", "STRING"),
                make_output_property("current_stage", "STRING"),
                make_output_property("selected_action", "STRING"),
                make_output_property("branch_focus", "STRING"),
                make_output_property("v_case_title", "STRING"),
                make_output_property("v_case_summary", "STRING"),
                make_output_property("focus_issues_json", "STRING"),
                make_output_property("claims_json", "STRING"),
                make_output_property("missing_evidence_json", "STRING"),
                make_output_property("opponent_arguments_json", "STRING"),
            ],
        )
    ]
    normalize["NextNodeIDs"] = [llm_id]
    patch_node_ui(
        normalize,
        normalize_id,
        x=560,
        y=250,
        source=True,
        target=True,
        output=[make_nodeui_output("Output", "OBJECT")],
        measured_height=108,
    )

    llm = find_sample_node(sample, "LLM", node_name="大模型2")
    llm["NodeID"] = llm_id
    llm["NodeName"] = "企鹅法庭推演"
    llm["NodeDesc"] = "根据标准化输入输出结构化庭审模拟结果"
    llm["LLMNodeData"]["Prompt"] = ""
    llm["LLMNodeData"]["SystemPrompt"] = LLM_SYSTEM_PROMPT
    llm["Inputs"] = [make_ref_input("normalized", "OBJECT", normalize_id, "Output", "标准化后的企鹅法庭输入对象")]
    llm["Outputs"] = [
        make_object_output(
            "Output",
            [
                make_output_property("Thought", "STRING", "大模型思考过程"),
                make_output_property("Content", "STRING", "大模型 JSON 字符串输出"),
            ],
        )
    ]
    llm["NextNodeIDs"] = [pack_id]
    llm["ExceptionHandling"] = {
        "Switch": "OFF",
        "MaxRetries": "3",
        "RetryInterval": "1",
        "AbnormalOutputResult": "",
        "HandleMethod": "EXCEPTION_OUTPUT",
        "NextNodeIDs": [],
        "AbnormalRetrySwitch": "ABNORMAL_RETRY_ON",
        "Timeout": "300",
    }
    llm["PendingMessage"] = {"Switch": "OFF", "Content": "", "DelaySeconds": "1"}
    patch_node_ui(
        llm,
        llm_id,
        x=930,
        y=250,
        source=True,
        target=True,
        measured_height=108,
        output=[
            {
                "id": new_id(),
                "value": "Output",
                "label": "Output",
                "_uiId": new_id(),
                "type": "OBJECT",
                "children": [
                    {
                        "id": new_id(),
                        "value": "Thought",
                        "label": "Thought",
                        "_uiId": new_id(),
                        "type": "STRING",
                        "children": [],
                    },
                    {
                        "id": new_id(),
                        "value": "Content",
                        "label": "Content",
                        "_uiId": new_id(),
                        "type": "STRING",
                        "children": [],
                    },
                ],
            }
        ],
        content="输出：Output、Output.Thought、Output.Content",
    )

    pack = find_sample_node(sample, "CODE_EXECUTOR")
    pack["NodeID"] = pack_id
    pack["NodeName"] = "统一封装结果"
    pack["NodeDesc"] = "解析模型输出，生成 reply 与结束节点共用的结果"
    pack["CodeExecutorNodeData"] = {"Code": PACK_CODE, "Language": "PYTHON3"}
    pack["Inputs"] = [
        make_ref_input("normalized", "OBJECT", normalize_id, "Output", "标准化输入"),
        make_ref_input("draft", "OBJECT", llm_id, "Output", "大模型结构化输出"),
    ]
    pack["Outputs"] = [
        make_object_output(
            "Output",
            [
                make_output_property("answer_text", "STRING"),
                make_output_property("result_json", "STRING"),
                make_output_property("stage", "STRING"),
                make_output_property("case_id", "STRING"),
                make_output_property("degraded_flags_json", "STRING"),
            ],
        )
    ]
    pack["NextNodeIDs"] = [reply_id]
    patch_node_ui(
        pack,
        pack_id,
        x=1290,
        y=250,
        source=True,
        target=True,
        output=[make_nodeui_output("Output", "OBJECT")],
        measured_height=108,
    )

    reply = find_sample_node(sample, "ANSWER")
    reply["NodeID"] = reply_id
    reply["NodeName"] = "回复用户"
    reply["NodeDesc"] = "向用户展示本轮企鹅法庭推演结果"
    reply["AnswerNodeData"] = {"Answer": "{{answer_text}}"}
    reply["Inputs"] = [
        make_ref_input("answer_text", "STRING", pack_id, "Output.answer_text", "回复给用户的 markdown"),
    ]
    reply["Outputs"] = [
        make_object_output(
            "Output",
            [
                make_output_property("reply_text", "STRING"),
            ],
        )
    ]
    reply["NextNodeIDs"] = [end_id]
    patch_node_ui(
        reply,
        reply_id,
        x=1640,
        y=220,
        source=True,
        target=True,
        output=[make_nodeui_output("Output", "OBJECT")],
        measured_height=88,
    )

    end = find_sample_node(sample, "END")
    end["NodeID"] = end_id
    end["NodeName"] = "结束"
    end["NodeDesc"] = "结束并对外暴露结构化结果"
    end["Outputs"] = [
        make_output_property("result_json", "STRING", "企鹅法庭结构化结果"),
        make_output_property("stage", "STRING", "当前阶段"),
        make_output_property("case_id", "STRING", "案件编号"),
        make_output_property("degraded_flags_json", "STRING", "降级标记"),
    ]
    end["Inputs"] = []
    end["NextNodeIDs"] = []
    patch_node_ui(
        end,
        end_id,
        x=1640,
        y=360,
        source=False,
        target=True,
        output=[],
        measured_height=88,
    )

    nodes = [start, normalize, llm, pack, reply, end]
    edges = [
        make_edge(start_id, normalize_id),
        make_edge(normalize_id, llm_id),
        make_edge(llm_id, pack_id),
        make_edge(pack_id, reply_id),
        make_edge(reply_id, end_id),
    ]

    workflow = {
        "ProtoVersion": "V2_6",
        "WorkflowID": workflow_id,
        "WorkflowName": "W00_企鹅法庭主控编排",
        "WorkflowDesc": (
            "描述：面向智慧法律场景的企鹅法庭主控工作流，完成案件输入标准化、"
            "庭审模拟、对方行为预判、风险分析与结果封装。"
            "示例：民间借贷纠纷进入举证阶段如何推进？劳动争议辩论阶段对方可能怎样抗辩？"
        ),
        "Nodes": nodes,
        "Edge": json.dumps(edges, ensure_ascii=False, separators=(",", ":")),
        "Mode": "NORMAL",
        "ReleaseTime": "",
        "UpdateTime": now_ms(),
    }

    return workflow, json_name


def column_name(index: int) -> str:
    result = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def build_shared_strings(rows: list[list[str]]) -> tuple[list[str], dict[str, int]]:
    shared: list[str] = []
    index_map: dict[str, int] = {}
    for row in rows:
        for cell in row:
            if cell not in index_map:
                index_map[cell] = len(shared)
                shared.append(cell)
    return shared, index_map


def build_sheet_xml(rows: list[list[str]], shared_index: dict[str, int]) -> str:
    last_col = column_name(max(len(row) for row in rows))
    last_row = len(rows)
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
        f"<dimension ref=\"A1:{last_col}{last_row}\"></dimension>",
        "<sheetViews><sheetView tabSelected=\"true\" workbookViewId=\"0\"></sheetView></sheetViews>",
        "<sheetFormatPr defaultRowHeight=\"15\"></sheetFormatPr>",
        "<sheetData>",
    ]
    for row_idx, row in enumerate(rows, start=1):
        parts.append(f"<row r=\"{row_idx}\">")
        for col_idx, cell in enumerate(row, start=1):
            ref = f"{column_name(col_idx)}{row_idx}"
            shared_id = shared_index[cell]
            parts.append(f"<c r=\"{ref}\" t=\"s\"><v>{shared_id}</v></c>")
        parts.append("</row>")
    parts.append("</sheetData></worksheet>")
    return "".join(parts)


def build_shared_strings_xml(shared: list[str]) -> str:
    body = "".join(f"<si><t>{escape(value)}</t></si>" for value in shared)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(shared)}" uniqueCount="{len(shared)}">{body}</sst>'
    )


def write_xlsx_from_template(template_name: str, rows: list[list[str]], dest: Path) -> None:
    template_path = SAMPLE_DIR / template_name
    with zipfile.ZipFile(template_path, "r") as src_zip:
        entries = {name: src_zip.read(name) for name in src_zip.namelist()}

    shared, shared_index = build_shared_strings(rows)
    entries["xl/sharedStrings.xml"] = build_shared_strings_xml(shared).encode("utf-8")
    entries["xl/worksheets/sheet1.xml"] = build_sheet_xml(rows, shared_index).encode("utf-8")

    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as out_zip:
        for name, data in entries.items():
            out_zip.writestr(name, data)


def validate_workflow(workflow: dict) -> None:
    node_ids = {node["NodeID"] for node in workflow["Nodes"]}
    for node in workflow["Nodes"]:
        for next_id in node.get("NextNodeIDs", []):
            if next_id not in node_ids:
                raise ValueError(f"invalid NextNodeID {next_id} in {node['NodeName']}")
    edge_list = json.loads(workflow["Edge"])
    for edge in edge_list:
        if edge["source"] not in node_ids or edge["target"] not in node_ids:
            raise ValueError(f"invalid edge {edge}")


def main() -> None:
    workflow, json_name = build_workflow()
    validate_workflow(workflow)

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    workflow_json_path = OUTPUT_DIR / json_name
    workflow_json_path.write_text(json.dumps(workflow, ensure_ascii=True, separators=(",", ":")), encoding="utf-8")

    workflow_id = workflow["WorkflowID"]
    write_xlsx_from_template(
        "workflows.xlsx",
        [
            ["工作流ID", "工作流名称", "工作流描述", "画布结构"],
            [workflow_id, workflow["WorkflowName"], workflow["WorkflowDesc"], json_name],
        ],
        OUTPUT_DIR / "工作流程.xlsx",
    )
    write_xlsx_from_template(
        "params.xlsx",
        [["工作流ID", "工作流节点ID", "工作流节点名称", "参数ID", "参数名称", "参数描述", "参数类型", "参数正确示例", "参数错误示例", "父参数ID"]],
        OUTPUT_DIR / "参数.xlsx",
    )
    write_xlsx_from_template(
        "vars.xlsx",
        [["工作流ID", "变量ID", "变量名称", "变量描述", "变量类型", "变量默认值", "变量默认值文件名称", "参数类型"]],
        OUTPUT_DIR / "变量.xlsx",
    )
    write_xlsx_from_template(
        "workflow_refs.xlsx",
        [["工作流ID", "工作流节点ID", "工作流引用ID", "工作流引用名称"]],
        OUTPUT_DIR / "工作流程引用.xlsx",
    )
    write_xlsx_from_template(
        "examples.xlsx",
        [
            ["工作流ID", "示例问法ID", "示例问法内容"],
            [workflow_id, new_id(), "我是原告，民间借贷纠纷已经进入举证阶段，请模拟下一轮庭审推进重点。"],
            [workflow_id, new_id(), "劳动争议案件到了辩论阶段，请预测对方可能抗辩并给我反驳要点。"],
            [workflow_id, new_id(), "请基于交通事故责任纠纷，输出本轮庭审复盘和胜诉率风险分析。"],
        ],
        OUTPUT_DIR / "示例问法.xlsx",
    )

    zip_path = OUTPUT_DIR.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as out_zip:
        for path in sorted(OUTPUT_DIR.iterdir()):
            out_zip.write(path, arcname=path.name)

    summary = {
        "workflow_id": workflow_id,
        "workflow_json": str(workflow_json_path),
        "package_dir": str(OUTPUT_DIR),
        "package_zip": str(zip_path),
        "node_count": len(workflow["Nodes"]),
        "edge_count": len(json.loads(workflow["Edge"])),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
