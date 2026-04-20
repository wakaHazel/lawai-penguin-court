from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class WorkflowAudit:
    workflow_id: str
    workflow_name: str
    file_name: str
    int_start_fields: list[str]
    llm_missing_outputs: list[str]
    broken_output_refs: list[str]
    plugin_dependencies: list[str]
    code_compile_errors: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Yuanqi workflow export zip contents.")
    parser.add_argument(
        "--dir",
        default="tmp/yuanqi_export_W00",
        help="Directory containing *_workflow.json files.",
    )
    return parser.parse_args()


def load_workflows(root: Path) -> dict[str, dict[str, Any]]:
    workflows: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("*_workflow.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        workflows[data["WorkflowID"]] = {
            "file": path,
            "data": data,
        }
    if not workflows:
        raise SystemExit(f"no workflow json found under {root}")
    return workflows


def collect_declared_output_paths(node: dict[str, Any]) -> set[str]:
    declared: set[str] = set()
    for output in node.get("Outputs", []):
        title = output.get("Title")
        if title != "Output":
            continue
        declared.add("Output")
        for prop in output.get("Properties", []):
            declared.add(f"Output.{prop['Title']}")
    return declared


def redact(value: str) -> str:
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def summarize_plugin_dependency(node: dict[str, Any]) -> str:
    plugin_data = (node.get("PluginNodeData") or {}).get("ToolInputs") or {}
    api = plugin_data.get("API") or {}
    headers = []
    for header in plugin_data.get("Header") or []:
        param_name = header.get("ParamName", "")
        values = ((header.get("Input") or {}).get("UserInputValue") or {}).get("Values") or []
        value = values[0] if values else ""
        if value:
            headers.append(f"{param_name}={redact(value)}")
        else:
            headers.append(f"{param_name}=<empty>")
    return f"{node['NodeName']} -> {api.get('Method', '')} {api.get('URL', '')} | headers: {', '.join(headers)}"


def audit_workflow(workflow_id: str, workflow: dict[str, Any], workflows: dict[str, dict[str, Any]]) -> WorkflowAudit:
    data = workflow["data"]
    nodes = data["Nodes"]
    node_by_id = {node["NodeID"]: node for node in nodes}
    start_node = next(node for node in nodes if node["NodeType"] == "START")

    int_start_fields = [item["Name"] for item in start_node.get("Inputs", []) if item["Type"] == "INT"]

    llm_missing_outputs = []
    for node in nodes:
        if node["NodeType"] == "LLM" and not collect_declared_output_paths(node):
            llm_missing_outputs.append(node["NodeName"])

    broken_output_refs = []
    for node in nodes:
        for input_item in node.get("Inputs", []):
            ref = ((input_item.get("Input") or {}).get("Reference") or {})
            ref_node_id = ref.get("NodeID")
            ref_path = ref.get("JsonPath")
            if not ref_node_id or not ref_path:
                continue
            ref_node = node_by_id.get(ref_node_id)
            if ref_node is None:
                continue
            if ref_node["NodeType"] == "START":
                continue
            declared_paths = collect_declared_output_paths(ref_node)
            if ref_path not in declared_paths:
                broken_output_refs.append(
                    f"{node['NodeName']}.{input_item['Name']} -> {ref_node['NodeName']}:{ref_path} "
                    f"(declared={sorted(declared_paths)})"
                )

    plugin_dependencies = [
        summarize_plugin_dependency(node)
        for node in nodes
        if node["NodeType"] == "PLUGIN"
    ]

    code_compile_errors = []
    for node in nodes:
        if node["NodeType"] != "CODE_EXECUTOR":
            continue
        code = ((node.get("CodeExecutorNodeData") or {}).get("Code") or "").strip()
        if not code:
            code_compile_errors.append(f"{node['NodeName']}: empty code body")
            continue
        try:
            compile(code, f"{data['WorkflowName']}::{node['NodeName']}", "exec")
        except SyntaxError as exc:
            code_compile_errors.append(
                f"{node['NodeName']}: SyntaxError line {exc.lineno}: {exc.msg}"
            )

    return WorkflowAudit(
        workflow_id=workflow_id,
        workflow_name=data["WorkflowName"],
        file_name=workflow["file"].name,
        int_start_fields=int_start_fields,
        llm_missing_outputs=llm_missing_outputs,
        broken_output_refs=broken_output_refs,
        plugin_dependencies=plugin_dependencies,
        code_compile_errors=code_compile_errors,
    )


def print_report(audits: list[WorkflowAudit]) -> None:
    print("# Yuanqi Workflow Zip Audit")
    for audit in audits:
        print()
        print(f"## {audit.workflow_name}")
        print(f"- file: {audit.file_name}")
        print(f"- workflow_id: {audit.workflow_id}")
        if audit.int_start_fields:
            print(f"- INT start fields: {', '.join(audit.int_start_fields)}")
        if audit.llm_missing_outputs:
            print(f"- LLM nodes missing output schema: {', '.join(audit.llm_missing_outputs)}")
        if audit.broken_output_refs:
            print("- Broken output references:")
            for item in audit.broken_output_refs:
                print(f"  - {item}")
        if audit.plugin_dependencies:
            print("- Plugin dependencies:")
            for item in audit.plugin_dependencies:
                print(f"  - {item}")
        if audit.code_compile_errors:
            print("- Code compile errors:")
            for item in audit.code_compile_errors:
                print(f"  - {item}")


def main() -> int:
    args = parse_args()
    root = Path(args.dir)
    workflows = load_workflows(root)
    audits = [
        audit_workflow(workflow_id, workflow, workflows)
        for workflow_id, workflow in sorted(workflows.items(), key=lambda item: item[1]["data"]["WorkflowName"])
    ]
    print_report(audits)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
