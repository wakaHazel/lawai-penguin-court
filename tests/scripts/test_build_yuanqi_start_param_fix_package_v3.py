import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.build_yuanqi_start_param_fix_package_v3 import (
    SOURCE_DIR,
    W00_UUID_TO_API_NAME,
    build_param_rows,
    build_w00_param_definitions,
    find_param_sheet_path,
    find_start_node,
    find_variable_sheet_path,
    load_sheet_rows,
    patch_w00_api_bindings,
    patch_workflow_params,
)


def load_workflow(file_name: str) -> dict:
    return json.loads((SOURCE_DIR / file_name).read_text(encoding="utf-8"))


def collect_custom_var_ids(payload):
    results = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key == "CustomVarID":
                results.append(value)
            results.extend(collect_custom_var_ids(value))
    elif isinstance(payload, list):
        for item in payload:
            results.extend(collect_custom_var_ids(item))
    return results


def test_find_sheet_paths_and_w00_param_names():
    variable_sheet = find_variable_sheet_path(SOURCE_DIR)
    param_sheet = find_param_sheet_path(SOURCE_DIR)

    assert variable_sheet.name.endswith(".xlsx")
    assert param_sheet.name.endswith(".xlsx")

    rows = load_sheet_rows(variable_sheet)
    definitions = build_w00_param_definitions(rows[1:])
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


def test_patch_w00_rebinds_all_target_uuids_to_api_names():
    rows = load_sheet_rows(find_variable_sheet_path(SOURCE_DIR))
    w00_params = build_w00_param_definitions(rows[1:])

    w00 = patch_workflow_params(
        load_workflow("6184ce77-a196-4111-a595-1ffba3383b0c_workflow.json"),
        w00_params,
    )
    patched = patch_w00_api_bindings(w00)
    start = find_start_node(patched)

    custom_var_ids = collect_custom_var_ids(patched)
    assert len(start["StartNodeData"]["WorkflowParams"]) == 11
    for raw_uuid, variable_name in W00_UUID_TO_API_NAME.items():
        assert raw_uuid not in custom_var_ids
        assert f"API.{variable_name}" in custom_var_ids


def test_build_param_rows_after_patch_has_expected_total():
    rows = load_sheet_rows(find_variable_sheet_path(SOURCE_DIR))
    w00_params = build_w00_param_definitions(rows[1:])

    workflows = []
    for path in sorted(SOURCE_DIR.glob("*_workflow.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        patched = patch_workflow_params(raw, w00_params)
        patched = patch_w00_api_bindings(patched)
        workflows.append({"path": path, "data": patched})

    param_rows = build_param_rows(workflows)
    assert len(param_rows) == 29
    assert param_rows[1][4] == "v_opponent_arguments"
    assert param_rows[-1][4] == "v_opponent_behavior"
