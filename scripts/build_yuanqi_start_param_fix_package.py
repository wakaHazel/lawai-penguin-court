from __future__ import annotations

import copy
import json
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


ROOT = Path(r"E:\lawai")
SOURCE_DIR = ROOT / "tmp" / "latest_export_W04_2026-04-17"
OUTPUT_DIR = ROOT / "exports" / "yuanqi_latest_start_params_fixed_2026-04-17"
OUTPUT_ZIP = ROOT / "exports" / "yuanqi_latest_start_params_fixed_2026-04-17.zip"
OUTPUT_ZIP_CN = ROOT / "exports" / "企鹅法庭元器导入包_最新启动参数修复版_2026-04-17.zip"

WORKFLOW_NAME_W00 = "W00_企鹅法庭主控编排"

XLSX_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"m": XLSX_NS, "r": REL_NS}

ET.register_namespace("", XLSX_NS)


def clone(value: dict) -> dict:
    return copy.deepcopy(value)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def find_start_node(workflow: dict) -> dict:
    return next(node for node in workflow["Nodes"] if node["NodeType"] == "START")


def load_workflows(root: Path) -> list[dict]:
    workflows = []
    for path in sorted(root.glob("*_workflow.json")):
        data = load_json(path)
        workflows.append({"path": path, "data": data})
    if not workflows:
        raise RuntimeError(f"no workflow json found under {root}")
    return workflows


def description_for_param(name: str) -> str:
    descriptions = {
        "case_id": "案件ID",
        "current_stage": "当前阶段",
        "selected_action": "上一动作",
        "round_number": "回合序号",
        "v_case_summary": "案件摘要",
        "v_case_type": "案件类型",
        "v_fact_keywords": "事实关键词",
        "v_focus_issues": "争议焦点",
        "v_historical_dialogs": "历史对话记录",
        "v_opponent_arguments": "对方抗辩要点",
        "v_opponent_role": "对方角色",
        "case_type": "案件类型",
        "focus_issues_json": "争议焦点JSON字符串",
        "fact_keywords_json": "事实关键词JSON字符串",
        "v_current_stage": "当前阶段",
        "v_selected_action": "上一动作",
        "v_likely_arguments": "对方可能抗辩",
        "v_case_profile": "案件画像",
        "v_legal_support_summary": "法律支持摘要",
        "v_simulation_timeline": "庭审模拟过程",
        "v_opponent_behavior": "对方行为模拟结果",
    }
    return descriptions.get(name, "-")


def example_for_param(name: str) -> str:
    examples = {
        "case_id": "CASE-001",
        "current_stage": "prepare",
        "selected_action": "submit_evidence",
        "round_number": "1",
        "v_case_summary": "申请人主张与公司存在劳动关系并请求支付双倍工资差额。",
        "v_case_type": "劳动争议",
        "v_fact_keywords": "工资流水,考勤记录,微信工作群记录",
        "v_focus_issues": "劳动关系是否成立；工资支付证据是否充分",
        "v_historical_dialogs": "第1回合：法官宣布开庭；原告陈述诉请。",
        "v_opponent_arguments": "双方系合作关系，不存在劳动关系。",
        "v_opponent_role": "defendant",
        "case_type": "劳动争议",
        "focus_issues_json": "[\"劳动关系是否成立\",\"工资支付证据是否充分\"]",
        "fact_keywords_json": "[\"工资流水\",\"考勤记录\",\"微信工作群记录\"]",
        "v_current_stage": "evidence",
        "v_selected_action": "challenge_authenticity",
        "v_likely_arguments": "双方系合作关系，不存在管理从属性。",
        "v_case_profile": "案情摘要、诉请与证据现状。",
        "v_legal_support_summary": "法条摘要、类案支持与证据建议。",
        "v_simulation_timeline": "第1回合至第3回合的关键互动记录。",
        "v_opponent_behavior": "对方主张、突袭证据与风险变化。",
    }
    return examples.get(name, "")


def build_param_definition(name: str, value_type: str) -> dict:
    return {
        "Name": name,
        "Type": value_type,
        "Desc": description_for_param(name),
        "IsRequired": False,
        "SubInputs": [],
        "DefaultValue": example_for_param(name),
        "DefaultFileName": "",
    }


def load_variable_sheet_rows(xlsx_path: Path) -> list[list[str]]:
    with zipfile.ZipFile(xlsx_path) as zf:
        shared_strings = read_shared_strings(zf)
        sheet_xml = resolve_first_sheet_xml(zf)
        root = ET.fromstring(sheet_xml)
        rows: list[list[str]] = []
        for row in root.findall(".//m:sheetData/m:row", NS):
            values: list[str] = []
            for cell in row.findall("m:c", NS):
                cell_type = cell.attrib.get("t")
                value_node = cell.find("m:v", NS)
                value = "" if value_node is None else value_node.text or ""
                if cell_type == "s" and value:
                    value = shared_strings[int(value)]
                values.append(value)
            rows.append(values)
        return rows


def read_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for node in root.findall("m:si", NS):
        values.append("".join(text.text or "" for text in node.findall(".//m:t", NS)))
    return values


def resolve_first_sheet_xml(zf: zipfile.ZipFile) -> bytes:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rid_to_target = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
    first_sheet = workbook.find("m:sheets", NS)[0]
    rid = first_sheet.attrib[f"{{{REL_NS}}}id"]
    return zf.read("xl/" + rid_to_target[rid])


def build_w00_param_definitions(variable_rows: Iterable[list[str]], workflow_id: str) -> list[dict]:
    definitions: list[dict] = []
    for row in variable_rows:
        if not row or row[0] != workflow_id:
            continue
        _, _, name, _, value_type, *_rest = row
        definitions.append(build_param_definition(name, value_type))
    if not definitions:
        raise RuntimeError("no W00 variable rows found for start param generation")
    return definitions


def build_param_rows(workflows: list[dict], w00_params: list[dict]) -> list[list[str]]:
    header = [
        "工作流ID",
        "工作流节点ID",
        "工作流节点名称",
        "参数ID",
        "参数名称",
        "参数描述",
        "参数类型",
        "参数正确示例",
        "参数错误示例",
        "父参数ID",
    ]
    rows = [header]
    for workflow in workflows:
        data = workflow["data"]
        start = find_start_node(data)
        if data["WorkflowName"] == WORKFLOW_NAME_W00:
            definitions = w00_params
        else:
            definitions = [
                build_param_definition(item["Name"], item["Type"])
                for item in start.get("Inputs", [])
            ]
        for item in definitions:
            rows.append(
                [
                    data["WorkflowID"],
                    start["NodeID"],
                    start["NodeName"],
                    str(uuid.uuid5(uuid.NAMESPACE_URL, f"yuanqi-param:{data['WorkflowID']}:{item['Name']}")),
                    item["Name"],
                    item["Desc"],
                    item["Type"],
                    item["DefaultValue"],
                    "",
                    "",
                ]
            )
    return rows


def patch_workflow_params(workflow: dict, w00_params: list[dict]) -> dict:
    patched = clone(workflow)
    start = find_start_node(patched)
    if patched["WorkflowName"] == WORKFLOW_NAME_W00:
        start["StartNodeData"]["WorkflowParams"] = clone(w00_params)
    else:
        start["StartNodeData"]["WorkflowParams"] = [
            build_param_definition(item["Name"], item["Type"])
            for item in start.get("Inputs", [])
        ]
    return patched


def column_ref(index: int) -> str:
    label = ""
    current = index
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        label = chr(65 + remainder) + label
    return label


def rebuild_shared_strings_xml(strings: list[str]) -> bytes:
    root = ET.Element(f"{{{XLSX_NS}}}sst", {"count": str(len(strings)), "uniqueCount": str(len(strings))})
    for text in strings:
        si = ET.SubElement(root, f"{{{XLSX_NS}}}si")
        t = ET.SubElement(si, f"{{{XLSX_NS}}}t")
        if text.strip() != text:
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        t.text = text
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def rebuild_sheet_xml(template_xml: bytes, rows: list[list[str]]) -> bytes:
    root = ET.fromstring(template_xml)
    sheet_data = root.find("m:sheetData", NS)
    if sheet_data is None:
        raise RuntimeError("sheetData not found in template xlsx")

    for child in list(sheet_data):
        sheet_data.remove(child)

    shared_strings: list[str] = []
    string_index: dict[str, int] = {}

    def get_string_id(value: str) -> int:
        if value not in string_index:
            string_index[value] = len(shared_strings)
            shared_strings.append(value)
        return string_index[value]

    max_col = 1
    for row_idx, row_values in enumerate(rows, start=1):
        row_node = ET.SubElement(sheet_data, f"{{{XLSX_NS}}}row", {"r": str(row_idx)})
        last_non_empty = 0
        for col_idx, value in enumerate(row_values, start=1):
            if value == "":
                continue
            last_non_empty = col_idx
            cell = ET.SubElement(
                row_node,
                f"{{{XLSX_NS}}}c",
                {"r": f"{column_ref(col_idx)}{row_idx}", "t": "s"},
            )
            value_node = ET.SubElement(cell, f"{{{XLSX_NS}}}v")
            value_node.text = str(get_string_id(str(value)))
        if last_non_empty:
            max_col = max(max_col, last_non_empty)

    dimension = root.find("m:dimension", NS)
    if dimension is not None:
        dimension.set("ref", f"A1:{column_ref(max_col)}{len(rows)}")

    return (
        ET.tostring(root, encoding="utf-8", xml_declaration=True),
        rebuild_shared_strings_xml(shared_strings),
    )


def rewrite_single_sheet_xlsx(xlsx_path: Path, rows: list[list[str]]) -> None:
    temp_path = xlsx_path.with_suffix(".tmp")
    with zipfile.ZipFile(xlsx_path, "r") as src:
        template_sheet_xml = resolve_first_sheet_xml(src)
        sheet_xml, shared_xml = rebuild_sheet_xml(template_sheet_xml, rows)
        first_sheet_name = "xl/worksheets/sheet1.xml"
        with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as dst:
            for item in src.infolist():
                if item.filename == first_sheet_name:
                    dst.writestr(first_sheet_name, sheet_xml)
                elif item.filename == "xl/sharedStrings.xml":
                    dst.writestr("xl/sharedStrings.xml", shared_xml)
                else:
                    dst.writestr(item, src.read(item.filename))
    temp_path.replace(xlsx_path)


def copy_source_package() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(SOURCE_DIR, OUTPUT_DIR)


def zip_output_dir() -> None:
    for zip_path in [OUTPUT_ZIP, OUTPUT_ZIP_CN]:
        if zip_path.exists():
            zip_path.unlink()
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(OUTPUT_DIR.rglob("*")):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(OUTPUT_DIR))
    shutil.copy2(OUTPUT_ZIP, OUTPUT_ZIP_CN)


def build_package() -> tuple[Path, Path]:
    copy_source_package()

    variable_xlsx = OUTPUT_DIR / "变量.xlsx"
    variable_rows = load_variable_sheet_rows(variable_xlsx)
    w00_workflow_id = variable_rows[1][0]
    w00_params = build_w00_param_definitions(variable_rows[1:], w00_workflow_id)

    workflows = load_workflows(OUTPUT_DIR)
    for workflow in workflows:
        patched = patch_workflow_params(workflow["data"], w00_params)
        write_json(workflow["path"], patched)
        workflow["data"] = patched

    parameter_rows = build_param_rows(workflows, w00_params)
    rewrite_single_sheet_xlsx(OUTPUT_DIR / "参数.xlsx", parameter_rows)

    zip_output_dir()
    return OUTPUT_DIR, OUTPUT_ZIP_CN


def main() -> None:
    output_dir, output_zip = build_package()
    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "output_zip": str(output_zip),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
