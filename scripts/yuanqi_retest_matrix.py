from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_API_URL = "https://yuanqi.tencent.com/openapi/v1/agent/chat/completions"
DEFAULT_CASE_ID = "case_live_verify_001"
DEFAULT_STAGES = ["prepare", "investigation", "evidence", "debate", "report_ready"]


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    default_db = repo_root / "data" / "penguin_court.db"

    parser = argparse.ArgumentParser(description="Retest Yuanqi published assistant routing.")
    parser.add_argument(
        "--assistant-id",
        default=os.getenv("YUANQI_APP_ID") or os.getenv("YUANQI_ASSISTANT_ID", ""),
        help="Published Yuanqi appid. Defaults to YUANQI_APP_ID or YUANQI_ASSISTANT_ID.",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("YUANQI_APP_KEY") or os.getenv("YUANQI_API_KEY", ""),
        help="Published Yuanqi appkey. Defaults to YUANQI_APP_KEY or YUANQI_API_KEY.",
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("YUANQI_API_URL", DEFAULT_API_URL),
        help="OpenAPI endpoint.",
    )
    parser.add_argument(
        "--case-id",
        default=DEFAULT_CASE_ID,
        help="Case id used in the message body and db lookup.",
    )
    parser.add_argument(
        "--db-path",
        default=str(default_db),
        help="SQLite db path used to build full W00 variables.",
    )
    return parser.parse_args()


def load_case_payload(db_path: str, case_id: str) -> dict[str, Any]:
    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(
            "select payload_json from cases where case_id = ?",
            (case_id,),
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        raise SystemExit(f"case_not_found: {case_id}")
    return json.loads(row[0])


def build_full_prepare_vars(case_payload: dict[str, Any]) -> dict[str, str]:
    opponent = case_payload.get("opponent_profile") or {}
    fact_keywords = (case_payload.get("core_facts") or []) + (case_payload.get("claims") or [])
    return {
        "case_id": str(case_payload.get("case_id") or ""),
        "current_stage": "prepare",
        "selected_action": "start simulation",
        "round_number": "1",
        "v_case_summary": str(case_payload.get("summary") or ""),
        "v_case_type": str(case_payload.get("case_type") or ""),
        "v_focus_issues": json.dumps(case_payload.get("focus_issues") or [], ensure_ascii=False),
        "v_fact_keywords": json.dumps(fact_keywords, ensure_ascii=False),
        "v_opponent_role": str(opponent.get("role") or "other"),
        "v_opponent_arguments": json.dumps(
            opponent.get("likely_arguments") or [],
            ensure_ascii=False,
        ),
        "v_historical_dialogs": "",
    }


def build_message_text(variables: dict[str, str]) -> str:
    return "\n".join(f"{key} = {value}" for key, value in variables.items())


def call_api(
    *,
    api_url: str,
    api_key: str,
    assistant_id: str,
    user_id: str,
    message_text: str,
) -> dict[str, Any]:
    payload = {
        "assistant_id": assistant_id,
        "user_id": user_id,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": message_text}],
            }
        ],
        "stream": False,
    }
    request = urllib.request.Request(
        api_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
            content = None
            if data.get("choices"):
                content = data["choices"][0].get("message", {}).get("content")
            return {
                "http_status": response.status,
                "output": data.get("output"),
                "content": content,
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"raw": body}
        return {
            "http_status": exc.code,
            "error": parsed,
        }


def main() -> int:
    args = parse_args()
    if not args.assistant_id:
        raise SystemExit("missing assistant id: use --assistant-id or YUANQI_APP_ID")
    if not args.api_key:
        raise SystemExit("missing api key: use --api-key or YUANQI_APP_KEY")

    case_payload = load_case_payload(args.db_path, args.case_id)
    full_prepare_vars = build_full_prepare_vars(case_payload)

    core_matrix = [
        ("A_case_only", f"case_id = {args.case_id}"),
        (
            "B_case_and_stage",
            build_message_text({"case_id": args.case_id, "current_stage": "prepare"}),
        ),
        ("C_full_w00", build_message_text(full_prepare_vars)),
    ]

    print("# core_matrix")
    for name, message_text in core_matrix:
        result = call_api(
            api_url=args.api_url,
            api_key=args.api_key,
            assistant_id=args.assistant_id,
            user_id=f"codex-{name}",
            message_text=message_text,
        )
        print(json.dumps({"name": name, **result}, ensure_ascii=False))

    print("# stage_matrix")
    for stage in DEFAULT_STAGES:
        result = call_api(
            api_url=args.api_url,
            api_key=args.api_key,
            assistant_id=args.assistant_id,
            user_id=f"codex-stage-{stage}",
            message_text=build_message_text({"case_id": args.case_id, "current_stage": stage}),
        )
        print(json.dumps({"stage": stage, **result}, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
