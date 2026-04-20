from __future__ import annotations

import copy
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(r"E:\lawai")
SOURCE_DIR = ROOT / "tmp" / "yuanqi_export_W02_2026-04-17"
OUTPUT_DIR = ROOT / "exports" / "yuanqi_local_patch_pkg_2026-04-17"
OUTPUT_ZIP = ROOT / "exports" / "yuanqi_local_patch_pkg_2026-04-17.zip"

W00_FILE = "0948102d-85b6-4ab5-a29f-a25be03ac178_workflow.json"
W02_FILE = "9e474aaa-7d9a-4f60-8dd4-b51abf4a95a4_workflow.json"
W04_FILE = "aaaab6c3-f250-4c73-ab68-9da834ea737d_workflow.json"

W00_LLM_2 = "a635a8e4-ae10-0959-938b-b848861d1bce"
W00_LLM_3 = "a0eac247-d07b-23e0-b5ba-08b086ff4f74"
W00_PACK = "f2e6c6e7-53c3-6103-78f2-d9d867369ef6"
W00_BRANCH_TRIAL = "24b2534a-35f5-29fd-be7c-b3aed985538a"

W02_CODE_1 = "5dc47a01-3fb2-77bb-9623-2afb4aec3f75"
W02_SEARCH_CASE = "991c0534-6795-27a3-c392-85c6f05f4d8f"
W02_SEARCH_LAW = "02072a10-689c-1d5e-7f15-3c0b8c61d057"

W04_LLM = "98c40431-6135-42dd-195e-aa5ca103ea61"


def clone(workflow: dict) -> dict:
    return copy.deepcopy(workflow)


def node_map(workflow: dict) -> dict[str, dict]:
    return {node["NodeID"]: node for node in workflow["Nodes"]}


def llm_output_schema() -> list[dict]:
    return [
        {
            "Title": "Output",
            "Type": "OBJECT",
            "Required": [],
            "Properties": [
                {
                    "Title": "Thought",
                    "Type": "STRING",
                    "Required": [],
                    "Properties": [],
                    "Desc": "",
                    "AnalysisMethod": "COVER",
                },
                {
                    "Title": "Content",
                    "Type": "STRING",
                    "Required": [],
                    "Properties": [],
                    "Desc": "",
                    "AnalysisMethod": "COVER",
                },
            ],
            "Desc": "standard llm output",
            "AnalysisMethod": "COVER",
        }
    ]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def set_plugin_page_size(node: dict, page_size: str) -> None:
    body = node["PluginNodeData"]["ToolInputs"]["Body"]
    page_size_param = next(item for item in body if item["ParamName"] == "pageSize")
    page_size_param["Input"]["UserInputValue"]["Values"] = [page_size]


def patch_w00_workflow(workflow: dict) -> dict:
    patched = clone(workflow)
    nodes = node_map(patched)

    nodes[W00_LLM_2]["Outputs"] = llm_output_schema()
    nodes[W00_LLM_3]["Outputs"] = llm_output_schema()

    nodes[W00_BRANCH_TRIAL]["CodeExecutorNodeData"]["Code"] = (
        "def main(params):\n"
        "    content = params.get('draft', '')\n"
        "    return {\n"
        "        'final_out': content,\n"
        "        'branch_name': 'trial'\n"
        "    }\n"
    )

    nodes[W00_PACK]["CodeExecutorNodeData"]["Code"] = (
        "def main(params):\n"
        "    pairs = [\n"
        "        (params.get('s1'), params.get('b1')),\n"
        "        (params.get('s2'), params.get('b2')),\n"
        "        (params.get('s3'), params.get('b3')),\n"
        "        (params.get('s4'), params.get('b4')),\n"
        "    ]\n"
        "    for value, branch in pairs:\n"
        "        text = str(value or '').strip()\n"
        "        name = str(branch or '').strip()\n"
        "        if text:\n"
        "            return {'final_out': text, 'branch_name': name}\n"
        "    return {'final_out': '', 'branch_name': ''}\n"
    )

    return patched


def patch_w02_workflow(workflow: dict) -> dict:
    patched = clone(workflow)
    nodes = node_map(patched)

    nodes[W02_CODE_1]["CodeExecutorNodeData"]["Code"] = (
        "def main(params):\n"
        "    import json\n"
        "\n"
        "    def parse_list(text, default_value):\n"
        "        raw = str(text or '').strip()\n"
        "        if not raw:\n"
        "            return [default_value]\n"
        "        try:\n"
        "            parsed = json.loads(raw)\n"
        "            if isinstance(parsed, list):\n"
        "                cleaned = [str(x).strip() for x in parsed if str(x).strip()]\n"
        "                if cleaned:\n"
        "                    return cleaned\n"
        "        except Exception:\n"
        "            pass\n"
        "        cleaned = [item.strip() for item in raw.split(',') if item.strip()]\n"
        "        return cleaned or [default_value]\n"
        "\n"
        "    return {\n"
        "        'issues_out': parse_list(params.get('issues_in'), '争议焦点待补充'),\n"
        "        'keywords_out': parse_list(params.get('keywords_in'), '案件关键词待补充'),\n"
        "    }\n"
    )

    set_plugin_page_size(nodes[W02_SEARCH_CASE], "3")
    set_plugin_page_size(nodes[W02_SEARCH_LAW], "3")

    return patched


def patch_w04_workflow(workflow: dict) -> dict:
    patched = clone(workflow)
    nodes = node_map(patched)
    nodes[W04_LLM]["Outputs"] = llm_output_schema()
    return patched


def copy_source_package() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(SOURCE_DIR, OUTPUT_DIR)


def zip_output_dir() -> None:
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(OUTPUT_DIR.rglob("*")):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(OUTPUT_DIR))


def build_package() -> tuple[Path, Path]:
    copy_source_package()

    w00_path = OUTPUT_DIR / W00_FILE
    w02_path = OUTPUT_DIR / W02_FILE
    w04_path = OUTPUT_DIR / W04_FILE

    write_json(w00_path, patch_w00_workflow(load_json(w00_path)))
    write_json(w02_path, patch_w02_workflow(load_json(w02_path)))
    write_json(w04_path, patch_w04_workflow(load_json(w04_path)))

    zip_output_dir()
    return OUTPUT_DIR, OUTPUT_ZIP


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
