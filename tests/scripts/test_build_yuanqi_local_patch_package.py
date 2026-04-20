import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.build_yuanqi_local_patch_package import (
    patch_w00_workflow,
    patch_w02_workflow,
    patch_w04_workflow,
)


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_patch_w00_replaces_concat_aggregator():
    workflow = load_json(
        r"E:\lawai\tmp\yuanqi_export_W02_2026-04-17\0948102d-85b6-4ab5-a29f-a25be03ac178_workflow.json"
    )
    patched = patch_w00_workflow(workflow)
    nodes = {node["NodeID"]: node for node in patched["Nodes"]}
    aggregator = nodes["f2e6c6e7-53c3-6103-78f2-d9d867369ef6"]
    code = aggregator["CodeExecutorNodeData"]["Code"]
    assert "s1 + s2 + s3 + s4" not in code
    assert "pairs = [" in code
    assert "return {'final_out': text, 'branch_name': name}" in code


def test_patch_w02_sets_page_size_to_3_and_json_first_normalization():
    workflow = load_json(
        r"E:\lawai\tmp\yuanqi_export_W02_2026-04-17\9e474aaa-7d9a-4f60-8dd4-b51abf4a95a4_workflow.json"
    )
    patched = patch_w02_workflow(workflow)
    nodes = {node["NodeID"]: node for node in patched["Nodes"]}
    code1 = nodes["5dc47a01-3fb2-77bb-9623-2afb4aec3f75"]["CodeExecutorNodeData"]["Code"]
    search_case = nodes["991c0534-6795-27a3-c392-85c6f05f4d8f"]
    search_law = nodes["02072a10-689c-1d5e-7f15-3c0b8c61d057"]
    assert "json.loads" in code1
    assert '"Values":["3"]' in json.dumps(search_case, ensure_ascii=False, separators=(",", ":"))
    assert '"Values":["3"]' in json.dumps(search_law, ensure_ascii=False, separators=(",", ":"))


def test_patch_w04_adds_llm_output_schema():
    workflow = load_json(
        r"E:\lawai\tmp\yuanqi_export_W02_2026-04-17\aaaab6c3-f250-4c73-ab68-9da834ea737d_workflow.json"
    )
    patched = patch_w04_workflow(workflow)
    nodes = {node["NodeID"]: node for node in patched["Nodes"]}
    llm = nodes["98c40431-6135-42dd-195e-aa5ca103ea61"]
    outputs = llm["Outputs"]
    assert outputs
    assert outputs[0]["Title"] == "Output"
    assert {item["Title"] for item in outputs[0]["Properties"]} >= {"Thought", "Content"}
