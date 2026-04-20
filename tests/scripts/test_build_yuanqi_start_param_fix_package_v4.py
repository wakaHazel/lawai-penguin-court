import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.build_yuanqi_start_param_fix_package_v4 import (
    API_PARAM_ORDER,
    NORMALIZER_NODE_ID,
    SOURCE_DIR,
    build_package,
)
from scripts.build_yuanqi_start_param_fix_package_v2 import load_sheet_rows
from scripts.build_yuanqi_start_param_fix_package_v3 import find_param_sheet_path


W00_FILE = "6184ce77-a196-4111-a595-1ffba3383b0c_workflow.json"


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


def load_built_w00() -> dict:
    output_dir, _ = build_package()
    return json.loads((output_dir / W00_FILE).read_text(encoding="utf-8"))


def test_w00_adds_normalizer_node_between_start_and_condition():
    workflow = load_built_w00()
    start = next(node for node in workflow["Nodes"] if node["NodeType"] == "START")
    normalizer = next(node for node in workflow["Nodes"] if node["NodeID"] == NORMALIZER_NODE_ID)

    assert start["NextNodeIDs"] == [NORMALIZER_NODE_ID]
    assert normalizer["NodeName"] == "API参数标准化"
    assert [item["Input"]["CustomVarID"] for item in normalizer["Inputs"]] == [
        f"API.{name}" for name in API_PARAM_ORDER
    ]


def test_w00_only_keeps_direct_api_refs_inside_normalizer_inputs():
    workflow = load_built_w00()
    node_by_id = {node["NodeID"]: node for node in workflow["Nodes"]}

    custom_var_ids = collect_custom_var_ids(workflow)
    assert sorted(custom_var_ids) == sorted(f"API.{name}" for name in API_PARAM_ORDER)

    for node in workflow["Nodes"]:
        if node["NodeID"] == NORMALIZER_NODE_ID:
            continue
        serialized = json.dumps(node, ensure_ascii=False)
        assert "API.case_id" not in serialized
        assert "API.current_stage" not in serialized
        assert "API.selected_action" not in serialized

    logic = next(node for node in workflow["Nodes"] if node["NodeType"] == "LOGIC_EVALUATOR")
    left = logic["LogicEvaluatorNodeData"]["Group"][0]["Logical"]["Comparison"]["Left"]
    assert left["InputType"] == "REFERENCE_OUTPUT"
    assert left["Reference"]["NodeID"] == NORMALIZER_NODE_ID
    assert left["Reference"]["JsonPath"] == "Output.current_stage"

    ref_node = next(node for node in workflow["Nodes"] if node["NodeType"] == "WORKFLOW_REF")
    ref_input = ref_node["WorkflowRefNodeData"]["RefInputs"][0]["Input"]
    assert ref_input["InputType"] == "REFERENCE_OUTPUT"
    assert ref_input["Reference"]["NodeID"] == NORMALIZER_NODE_ID


def test_build_package_preserves_param_sheet_shape():
    output_dir, _ = build_package()
    param_sheet = find_param_sheet_path(output_dir)
    rows = load_sheet_rows(param_sheet)

    assert len(rows) == 29
    assert rows[1][4] == "v_opponent_arguments"
    assert rows[-1][4] == "v_opponent_behavior"
