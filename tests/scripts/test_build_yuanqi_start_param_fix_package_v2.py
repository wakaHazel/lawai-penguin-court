import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.build_yuanqi_start_param_fix_package_v2 import (
    WORKFLOW_NAME_W00,
    build_param_rows,
    build_w00_param_definitions,
    find_start_node,
    load_sheet_rows,
    patch_llm_and_logic,
    patch_workflow_params,
    rewrite_single_sheet_xlsx,
)


LATEST_DIR = Path(r"E:\lawai\tmp\latest_export_W04_2026-04-17")


def load_workflow(file_name: str) -> dict:
    return json.loads((LATEST_DIR / file_name).read_text(encoding="utf-8"))


def test_w00_param_names_match_latest_variable_sheet():
    rows = load_sheet_rows(LATEST_DIR / "变量.xlsx")
    definitions = build_w00_param_definitions(rows[1:], rows[1][0])
    assert [item["Name"] for item in definitions] == [
        "v_opponent_arguments",
        "v_case_summary",
        "v_fact_keywords",
        "round_number",
        "v_historical_dialogs",
        "v_opponent_role",
        "current_stage",
        "case_id",
        "v_focus_issues",
        "v_case_type",
        "selected_action",
    ]


def test_patch_workflow_params_and_llm_outputs():
    rows = load_sheet_rows(LATEST_DIR / "变量.xlsx")
    w00_params = build_w00_param_definitions(rows[1:], rows[1][0])

    w00 = patch_llm_and_logic(
        patch_workflow_params(
            load_workflow("6184ce77-a196-4111-a595-1ffba3383b0c_workflow.json"),
            w00_params,
        )
    )
    w04 = patch_llm_and_logic(
        patch_workflow_params(
            load_workflow("ddce973e-a36f-44c7-93a3-32fadfbba27b_workflow.json"),
            w00_params,
        )
    )

    w00_start = find_start_node(w00)
    w04_start = find_start_node(w04)

    assert w00["WorkflowName"] == WORKFLOW_NAME_W00
    assert len(w00_start["StartNodeData"]["WorkflowParams"]) == 11
    assert len(w04_start["StartNodeData"]["WorkflowParams"]) == 4

    w00_nodes = {node["NodeID"]: node for node in w00["Nodes"]}
    w04_nodes = {node["NodeID"]: node for node in w04["Nodes"]}
    assert w00_nodes["a635a8e4-ae10-0959-938b-b848861d1bce"]["Outputs"][0]["Title"] == "Output"
    assert w00_nodes["a0eac247-d07b-23e0-b5ba-08b086ff4f74"]["Outputs"][0]["Title"] == "Output"
    assert w04_nodes["98c40431-6135-42dd-195e-aa5ca103ea61"]["Outputs"][0]["Title"] == "Output"


def test_build_param_rows_and_rewrite_xlsx_round_trip(tmp_path):
    rows = load_sheet_rows(LATEST_DIR / "变量.xlsx")
    w00_params = build_w00_param_definitions(rows[1:], rows[1][0])

    workflows = []
    for path in sorted(LATEST_DIR.glob("*_workflow.json")):
        workflows.append({"path": path, "data": json.loads(path.read_text(encoding="utf-8"))})

    param_rows = build_param_rows(workflows, w00_params)
    assert len(param_rows) == 29

    copied = tmp_path / "参数.xlsx"
    shutil.copy2(LATEST_DIR / "参数.xlsx", copied)
    rewrite_single_sheet_xlsx(copied, param_rows)
    round_trip_rows = load_sheet_rows(copied)

    assert round_trip_rows[0] == param_rows[0]
    assert round_trip_rows[1][4] == "v_opponent_arguments"
    assert round_trip_rows[-1][4] == "v_opponent_behavior"
