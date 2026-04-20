import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.build_yuanqi_start_param_fix_package import (
    WORKFLOW_NAME_W00,
    build_param_rows,
    build_w00_param_definitions,
    find_start_node,
    load_variable_sheet_rows,
    patch_workflow_params,
    rewrite_single_sheet_xlsx,
)


LATEST_DIR = Path(r"E:\lawai\tmp\latest_export_W04_2026-04-17")


def load_workflow(file_name: str) -> dict:
    return json.loads((LATEST_DIR / file_name).read_text(encoding="utf-8"))


def test_w00_param_names_match_latest_variable_sheet():
    rows = load_variable_sheet_rows(LATEST_DIR / "变量.xlsx")
    workflow_id = rows[1][0]
    definitions = build_w00_param_definitions(rows[1:], workflow_id)
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


def test_patch_workflow_params_populates_w00_and_subflows():
    rows = load_variable_sheet_rows(LATEST_DIR / "变量.xlsx")
    workflow_id = rows[1][0]
    w00_params = build_w00_param_definitions(rows[1:], workflow_id)

    w00 = patch_workflow_params(
        load_workflow("6184ce77-a196-4111-a595-1ffba3383b0c_workflow.json"),
        w00_params,
    )
    w01 = patch_workflow_params(
        load_workflow("ccd3e9ee-c1b8-4f80-8156-9d06ab982758_workflow.json"),
        w00_params,
    )

    w00_start = find_start_node(w00)
    w01_start = find_start_node(w01)

    assert w00["WorkflowName"] == WORKFLOW_NAME_W00
    assert len(w00_start["StartNodeData"]["WorkflowParams"]) == 11
    assert [item["Name"] for item in w01_start["StartNodeData"]["WorkflowParams"]] == [
        "current_stage",
        "v_case_summary",
        "round_number",
        "v_historical_dialogs",
    ]


def test_build_param_rows_and_rewrite_xlsx_round_trip(tmp_path):
    rows = load_variable_sheet_rows(LATEST_DIR / "变量.xlsx")
    workflow_id = rows[1][0]
    w00_params = build_w00_param_definitions(rows[1:], workflow_id)

    workflows = []
    for path in sorted(LATEST_DIR.glob("*_workflow.json")):
        workflows.append({"path": path, "data": json.loads(path.read_text(encoding="utf-8"))})

    param_rows = build_param_rows(workflows, w00_params)
    assert len(param_rows) == 29

    copied = tmp_path / "参数.xlsx"
    shutil.copy2(LATEST_DIR / "参数.xlsx", copied)
    rewrite_single_sheet_xlsx(copied, param_rows)
    round_trip_rows = load_variable_sheet_rows(copied)

    assert round_trip_rows[0] == param_rows[0]
    assert round_trip_rows[1][4] == "v_opponent_arguments"
    assert round_trip_rows[-1][4] == "v_opponent_behavior"
