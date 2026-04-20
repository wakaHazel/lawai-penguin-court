from __future__ import annotations

import json
import shutil
import sys
import uuid
import zipfile
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_yuanqi_start_param_fix_package_v2 import (
    load_sheet_rows,
    load_workflows,
    patch_llm_and_logic,
    rewrite_single_sheet_xlsx,
    write_json,
)


ROOT = Path(r"E:\lawai")
SOURCE_DIR = ROOT / "tmp" / "latest_export_W04_2026-04-17"
OUTPUT_DIR = ROOT / "exports" / "yuanqi_latest_api_binding_fix_2026-04-17"
OUTPUT_ZIP = ROOT / "exports" / "yuanqi_latest_api_binding_fix_2026-04-17.zip"
OUTPUT_ZIP_CN = ROOT / "exports" / "企鹅法庭元器导入包_API绑定修复版_2026-04-17.zip"

W00_WORKFLOW_ID = "6184ce77-a196-4111-a595-1ffba3383b0c"

PARAM_HEADER = [
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

VARIABLE_HEADER_PREFIX = ["工作流ID", "变量ID", "变量名称", "变量描述"]

W00_UUID_TO_API_NAME = {
    "02d43d74-2b97-42bc-8f50-ecce0dd5d79d": "v_opponent_arguments",
    "06dff05a-f901-446f-af6a-c53ba4741d48": "v_case_summary",
    "150d957f-dd28-4a2e-84c2-dac15d7f56ab": "v_fact_keywords",
    "1f33cbf1-a6df-4424-8bd5-22884f996954": "round_number",
    "3c51606c-3599-4888-b9c2-cdaa822405e1": "v_historical_dialogs",
    "44f1fab3-5df0-458f-9ae1-cd57e3310edd": "v_opponent_role",
    "47f22771-6a44-47a6-b560-ad074db1251b": "current_stage",
    "5deba3cc-5cf8-4319-88fd-5b12497fb934": "case_id",
    "9bd258db-b2ab-44cb-bb46-d9a4946742cf": "v_focus_issues",
    "abf17397-52e0-419b-8f27-bf8f71c44f06": "v_case_type",
    "fb7c58b5-e068-4852-98b3-528ef535a76b": "selected_action",
}


def clone_json(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def find_start_node(workflow: dict) -> dict:
    return next(node for node in workflow["Nodes"] if node["NodeType"] == "START")


def find_variable_sheet_path(root: Path) -> Path:
    for path in sorted(root.glob("*.xlsx")):
        rows = load_sheet_rows(path)
        if rows and rows[0][:4] == VARIABLE_HEADER_PREFIX:
            return path
    raise RuntimeError(f"variable sheet not found under {root}")


def find_param_sheet_path(root: Path) -> Path:
    for path in sorted(root.glob("*.xlsx")):
        rows = load_sheet_rows(path)
        if rows and rows[0] == PARAM_HEADER:
            return path
    raise RuntimeError(f"param sheet not found under {root}")


def build_param_definition(name: str, value_type: str, desc: str = "") -> dict:
    return {
        "Name": name,
        "Type": value_type,
        "Desc": desc or name,
        "IsRequired": False,
        "SubInputs": [],
        "DefaultValue": "",
        "DefaultFileName": "",
    }


def build_w00_param_definitions(variable_rows: list[list[str]]) -> list[dict]:
    definitions: list[dict] = []
    for row in variable_rows:
        if not row or row[0] != W00_WORKFLOW_ID:
            continue
        _, _, variable_name, variable_desc, variable_type, *_ = row
        definitions.append(build_param_definition(variable_name, variable_type, variable_desc))
    if not definitions:
        raise RuntimeError("no W00 variable rows found in variable sheet")
    return definitions


def build_start_param_definitions(start_node: dict) -> list[dict]:
    return [
        build_param_definition(item["Name"], item["Type"], item.get("Desc", ""))
        for item in start_node.get("Inputs", [])
    ]


def patch_workflow_params(workflow: dict, w00_params: list[dict]) -> dict:
    patched = clone_json(workflow)
    start = find_start_node(patched)
    if patched["WorkflowID"] == W00_WORKFLOW_ID:
        start.setdefault("StartNodeData", {})
        start["StartNodeData"]["WorkflowParams"] = clone_json(w00_params)
    else:
        start.setdefault("StartNodeData", {})
        start["StartNodeData"]["WorkflowParams"] = build_start_param_definitions(start)
    return patched


def replace_custom_var_ids(payload: Any, uuid_to_name: dict[str, str]) -> Any:
    if isinstance(payload, dict):
        replaced = {}
        for key, value in payload.items():
            if key == "CustomVarID" and isinstance(value, str) and value in uuid_to_name:
                replaced[key] = f"API.{uuid_to_name[value]}"
            else:
                replaced[key] = replace_custom_var_ids(value, uuid_to_name)
        return replaced
    if isinstance(payload, list):
        return [replace_custom_var_ids(item, uuid_to_name) for item in payload]
    return payload


def patch_w00_api_bindings(workflow: dict) -> dict:
    if workflow["WorkflowID"] != W00_WORKFLOW_ID:
        return workflow
    return replace_custom_var_ids(workflow, W00_UUID_TO_API_NAME)


def build_param_rows(workflows: list[dict]) -> list[list[str]]:
    rows = [PARAM_HEADER]
    for workflow in workflows:
        data = workflow["data"]
        start = find_start_node(data)
        params = start.get("StartNodeData", {}).get("WorkflowParams", [])
        for item in params:
            rows.append(
                [
                    data["WorkflowID"],
                    start["NodeID"],
                    start["NodeName"],
                    str(uuid.uuid5(uuid.NAMESPACE_URL, f"yuanqi-param:{data['WorkflowID']}:{item['Name']}")),
                    item["Name"],
                    item.get("Desc", "") or item["Name"],
                    item["Type"],
                    item.get("DefaultValue", ""),
                    "",
                    "",
                ]
            )
    return rows


def copy_source_package() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(SOURCE_DIR, OUTPUT_DIR)


def zip_output_dir() -> None:
    for path in (OUTPUT_ZIP, OUTPUT_ZIP_CN):
        if path.exists():
            path.unlink()
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(OUTPUT_DIR.rglob("*")):
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(OUTPUT_DIR))
    shutil.copy2(OUTPUT_ZIP, OUTPUT_ZIP_CN)


def build_package() -> tuple[Path, Path]:
    copy_source_package()

    variable_sheet = find_variable_sheet_path(OUTPUT_DIR)
    param_sheet = find_param_sheet_path(OUTPUT_DIR)
    variable_rows = load_sheet_rows(variable_sheet)
    w00_params = build_w00_param_definitions(variable_rows[1:])

    workflows = load_workflows(OUTPUT_DIR)
    for workflow in workflows:
        patched = patch_workflow_params(workflow["data"], w00_params)
        patched = patch_w00_api_bindings(patched)
        patched = patch_llm_and_logic(patched)
        write_json(workflow["path"], patched)
        workflow["data"] = patched

    param_rows = build_param_rows(workflows)
    rewrite_single_sheet_xlsx(param_sheet, param_rows)

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
