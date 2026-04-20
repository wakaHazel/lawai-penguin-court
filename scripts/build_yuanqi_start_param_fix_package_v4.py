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
from scripts.build_yuanqi_start_param_fix_package_v3 import (
    W00_UUID_TO_API_NAME,
    build_param_definition,
    build_param_rows,
    build_w00_param_definitions,
    find_param_sheet_path,
    find_start_node,
    find_variable_sheet_path,
)


ROOT = Path(r"E:\lawai")
SOURCE_DIR = ROOT / "tmp" / "latest_export_W04_2026-04-17"
OUTPUT_DIR = ROOT / "exports" / "yuanqi_latest_api_contract_fix_2026-04-17"
OUTPUT_ZIP = ROOT / "exports" / "yuanqi_latest_api_contract_fix_2026-04-17.zip"
OUTPUT_ZIP_CN = ROOT / "exports" / "\u4f01\u9e45\u6cd5\u5ead\u5143\u5668\u5bfc\u5165\u5305_API\u53c2\u6570\u5951\u7ea6\u4fee\u590d\u7248_2026-04-17.zip"

W00_WORKFLOW_ID = "6184ce77-a196-4111-a595-1ffba3383b0c"
NORMALIZER_NODE_ID = "0c9c5a56-75ef-4d12-9d4c-0d7c18fd8e20"
NORMALIZER_NODE_NAME = "API\u53c2\u6570\u6807\u51c6\u5316"

API_PARAM_ORDER = [
    "case_id",
    "current_stage",
    "round_number",
    "selected_action",
    "v_case_summary",
    "v_case_type",
    "v_fact_keywords",
    "v_focus_issues",
    "v_historical_dialogs",
    "v_opponent_arguments",
    "v_opponent_role",
]

NORMALIZED_OUTPUT_FIELDS = API_PARAM_ORDER + [
    "case_type",
    "fact_keywords_json",
    "focus_issues_json",
    "opponent_arguments_json",
]


def clone_json(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def node_map(workflow: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {node["NodeID"]: node for node in workflow["Nodes"]}


def reference_output(field_name: str) -> dict[str, Any]:
    return {
        "InputType": "REFERENCE_OUTPUT",
        "Reference": {
            "NodeID": NORMALIZER_NODE_ID,
            "JsonPath": f"Output.{field_name}",
        },
    }


def api_input(field_name: str) -> dict[str, Any]:
    return {
        "InputType": "CUSTOM_VARIABLE",
        "CustomVarID": f"API.{field_name}",
    }


def output_property(field_name: str) -> dict[str, Any]:
    return {
        "Title": field_name,
        "Type": "STRING",
        "Required": [],
        "Properties": [],
        "Desc": field_name,
        "AnalysisMethod": "COVER",
    }


def normalizer_outputs() -> list[dict[str, Any]]:
    return [
        {
            "Title": "Output",
            "Type": "OBJECT",
            "Required": [],
            "Properties": [output_property(name) for name in NORMALIZED_OUTPUT_FIELDS],
            "Desc": "Normalized API input object",
            "AnalysisMethod": "COVER",
        }
    ]


def normalizer_code() -> str:
    return (
        "def main(params: dict) -> dict:\n"
        "    def text(name: str, default: str = '') -> str:\n"
        "        value = params.get(name)\n"
        "        if value is None:\n"
        "            return default\n"
        "        value = str(value).strip()\n"
        "        return value if value else default\n"
        "\n"
        "    result = {\n"
        "        'case_id': text('case_id', 'CASE-001'),\n"
        "        'current_stage': text('current_stage', 'prepare'),\n"
        "        'round_number': text('round_number', '1'),\n"
        "        'selected_action': text('selected_action', 'start'),\n"
        "        'v_case_summary': text('v_case_summary', 'case summary pending'),\n"
        "        'v_case_type': text('v_case_type', 'civil case'),\n"
        "        'v_fact_keywords': text('v_fact_keywords', '[]'),\n"
        "        'v_focus_issues': text('v_focus_issues', '[]'),\n"
        "        'v_historical_dialogs': text('v_historical_dialogs', ''),\n"
        "        'v_opponent_arguments': text('v_opponent_arguments', '[]'),\n"
        "        'v_opponent_role': text('v_opponent_role', 'defendant'),\n"
        "    }\n"
        "    result['case_type'] = result['v_case_type']\n"
        "    result['fact_keywords_json'] = result['v_fact_keywords']\n"
        "    result['focus_issues_json'] = result['v_focus_issues']\n"
        "    result['opponent_arguments_json'] = result['v_opponent_arguments']\n"
        "    return result\n"
    )


def build_normalizer_node(start_node: dict[str, Any], condition_node: dict[str, Any]) -> dict[str, Any]:
    inputs = [
        {
            **build_param_definition(name, "STRING", name),
            "Input": api_input(name),
        }
        for name in API_PARAM_ORDER
    ]
    node_ui = {
        "data": {
            "content": NORMALIZER_NODE_NAME,
            "isHovering": False,
            "isParallel": False,
            "source": True,
            "target": True,
            "debug": None,
            "error": False,
            "output": [
                {
                    "label": "Output",
                    "desc": "normalized api params",
                    "optionType": "REFERENCE_OUTPUT",
                    "type": "OBJECT",
                    "children": [],
                }
            ],
            "schema": None,
            "checkDataError": 0,
            "showTips": False,
            "isConcurrent": False,
            "financeType": None,
            "connectedHandles": {
                f"{NORMALIZER_NODE_ID}-target": True,
                f"{NORMALIZER_NODE_ID}-source": True,
            },
        },
        "position": {
            "x": 900,
            "y": 412,
        },
        "targetPosition": "left",
        "sourcePosition": "right",
        "selected": False,
        "measured": {
            "width": 254,
            "height": 108,
        },
    }
    return {
        "NodeID": NORMALIZER_NODE_ID,
        "NodeName": NORMALIZER_NODE_NAME,
        "NodeDesc": "Bind all Yuanqi API start parameters once, then expose stable normalized outputs.",
        "NodeType": "CODE_EXECUTOR",
        "CodeExecutorNodeData": {
            "Code": normalizer_code(),
        },
        "Inputs": inputs,
        "Outputs": normalizer_outputs(),
        "NextNodeIDs": [condition_node["NodeID"]],
        "NodeUI": json.dumps(node_ui, ensure_ascii=False, separators=(",", ":")),
    }


def build_edge(source: str, target: str, source_handle: str | None = None, target_handle: str | None = None) -> dict[str, Any]:
    source_handle = source_handle or f"{source}-source"
    target_handle = target_handle or f"{target}-target"
    return {
        "source": source,
        "sourceHandle": source_handle,
        "target": target,
        "targetHandle": target_handle,
        "type": "custom",
        "data": {
            "connectedNodeIsHovering": False,
            "error": False,
            "isHovering": False,
        },
        "id": f"xy-edge__{source}{source_handle}-{target}{target_handle}",
        "selected": False,
        "animated": False,
    }


def patch_start_to_normalizer(workflow: dict[str, Any]) -> dict[str, Any]:
    patched = clone_json(workflow)
    nodes = node_map(patched)
    start = find_start_node(patched)
    condition = next(node for node in patched["Nodes"] if node["NodeType"] == "LOGIC_EVALUATOR")

    if NORMALIZER_NODE_ID not in nodes:
        start_index = patched["Nodes"].index(start)
        patched["Nodes"].insert(start_index + 1, build_normalizer_node(start, condition))

    start["NextNodeIDs"] = [NORMALIZER_NODE_ID]

    edges = json.loads(patched.get("Edge") or "[]")
    edges = [
        edge
        for edge in edges
        if not (edge.get("source") == start["NodeID"] and edge.get("target") == condition["NodeID"])
        and not (edge.get("source") == start["NodeID"] and edge.get("target") == NORMALIZER_NODE_ID)
        and not (edge.get("source") == NORMALIZER_NODE_ID and edge.get("target") == condition["NodeID"])
    ]
    edges.insert(0, build_edge(start["NodeID"], NORMALIZER_NODE_ID))
    edges.insert(1, build_edge(NORMALIZER_NODE_ID, condition["NodeID"]))
    patched["Edge"] = json.dumps(edges, ensure_ascii=False, separators=(",", ":"))
    return patched


def custom_variable_name(custom_var_id: str) -> str | None:
    if custom_var_id in W00_UUID_TO_API_NAME:
        return W00_UUID_TO_API_NAME[custom_var_id]
    if custom_var_id.startswith("API."):
        name = custom_var_id.removeprefix("API.")
        if name in API_PARAM_ORDER:
            return name
    return None


def replace_direct_api_refs(payload: Any) -> Any:
    if isinstance(payload, dict):
        input_type = payload.get("InputType")
        custom_var_id = payload.get("CustomVarID")
        if input_type == "CUSTOM_VARIABLE" and isinstance(custom_var_id, str):
            name = custom_variable_name(custom_var_id)
            if name is not None:
                return reference_output(name)
        return {key: replace_direct_api_refs(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [replace_direct_api_refs(item) for item in payload]
    return payload


def patch_w00_api_contract(workflow: dict[str, Any]) -> dict[str, Any]:
    if workflow["WorkflowID"] != W00_WORKFLOW_ID:
        return workflow

    patched = patch_start_to_normalizer(workflow)
    normalizer = next(node for node in patched["Nodes"] if node["NodeID"] == NORMALIZER_NODE_ID)

    for node in patched["Nodes"]:
        if node["NodeID"] == NORMALIZER_NODE_ID:
            continue
        for key in list(node.keys()):
            node[key] = replace_direct_api_refs(node[key])
        if isinstance(node.get("NodeUI"), str):
            node["NodeUI"] = node["NodeUI"].replace(
                "API.current_stage",
                f"{NORMALIZER_NODE_NAME}.Output.current_stage",
            )

    normalizer["Inputs"] = [
        {
            **build_param_definition(name, "STRING", name),
            "Input": api_input(name),
        }
        for name in API_PARAM_ORDER
    ]
    normalizer["Outputs"] = normalizer_outputs()
    normalizer.setdefault("CodeExecutorNodeData", {})["Code"] = normalizer_code()
    return patched


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
        patched = workflow["data"]
        start = find_start_node(patched)
        if patched["WorkflowID"] == W00_WORKFLOW_ID:
            start.setdefault("StartNodeData", {})
            start["StartNodeData"]["WorkflowParams"] = clone_json(w00_params)
            patched = patch_w00_api_contract(patched)
        else:
            start.setdefault("StartNodeData", {})
            start["StartNodeData"]["WorkflowParams"] = [
                build_param_definition(item["Name"], item["Type"], item.get("Desc", ""))
                for item in start.get("Inputs", [])
            ]
        patched = patch_llm_and_logic(patched)
        write_json(workflow["path"], patched)
        workflow["data"] = patched

    rewrite_single_sheet_xlsx(param_sheet, build_param_rows(workflows))
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
