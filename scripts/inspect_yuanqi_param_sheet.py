from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET


XLSX_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"m": XLSX_NS, "r": REL_NS}

PARAM_HEADER = ["工作流ID", "工作流节点ID", "工作流节点名称", "参数ID"]


def read_rows(xlsx: Path) -> list[list[str]]:
    with ZipFile(xlsx) as zf:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for node in root.findall("m:si", NS):
                shared_strings.append("".join(t.text or "" for t in node.findall(".//m:t", NS)))

        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rid_to_target = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
        first_sheet = workbook.find("m:sheets", NS)[0]
        rid = first_sheet.attrib[f"{{{REL_NS}}}id"]
        sheet_path = "xl/" + rid_to_target[rid]
        root = ET.fromstring(zf.read(sheet_path))

        rows: list[list[str]] = []
        for row in root.findall(".//m:sheetData/m:row", NS):
            values: list[str] = []
            for cell in row.findall("m:c", NS):
                cell_type = cell.attrib.get("t")
                value_node = cell.find("m:v", NS)
                value = "" if value_node is None else (value_node.text or "")
                if cell_type == "s" and value:
                    value = shared_strings[int(value)]
                values.append(value)
            rows.append(values)
        return rows


def find_param_sheet(base: Path) -> Path:
    for path in sorted(base.glob("*.xlsx")):
        rows = read_rows(path)
        if rows and rows[0][:4] == PARAM_HEADER:
            return path
    raise RuntimeError(f"param sheet not found under {base}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True)
    args = parser.parse_args()

    base = Path(args.dir)
    param_sheet = find_param_sheet(base)
    rows = read_rows(param_sheet)

    by_node: dict[str, list[str]] = defaultdict(list)
    for row in rows[1:]:
        if not row:
            continue
        node_name = row[2]
        param_name = row[4]
        by_node[node_name].append(param_name)

    payload = {
        "param_sheet": str(param_sheet),
        "total_rows": len(rows),
        "node_counts": Counter({node: len(params) for node, params in by_node.items()}),
        "node_params": by_node,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
