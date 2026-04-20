from __future__ import annotations

from ..database import get_connection
from ..schemas.case import CaseProfile


def save_case(case_profile: CaseProfile) -> CaseProfile:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO cases (
                case_id,
                domain,
                case_type,
                title,
                summary,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(case_id) DO UPDATE SET
                domain = excluded.domain,
                case_type = excluded.case_type,
                title = excluded.title,
                summary = excluded.summary,
                payload_json = excluded.payload_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                case_profile.case_id,
                case_profile.domain.value,
                case_profile.case_type.value,
                case_profile.title,
                case_profile.summary,
                case_profile.model_dump_json(),
            ),
        )
    return case_profile.model_copy(deep=True)


def get_case(case_id: str) -> CaseProfile | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT payload_json
            FROM cases
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

    if row is None:
        return None
    return CaseProfile.model_validate_json(row["payload_json"])


def list_cases(limit: int = 100) -> list[CaseProfile]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT payload_json
            FROM cases
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [CaseProfile.model_validate_json(row["payload_json"]) for row in rows]
