from __future__ import annotations

from ..database import get_connection
from ..schemas.analysis import ReplayReportSnapshot


def save_replay_report(report: ReplayReportSnapshot) -> ReplayReportSnapshot:
    report_id = f"{report.case_id}:{report.simulation_id}"
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO replay_reports (
                report_id,
                case_id,
                simulation_id,
                generated_at,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(report_id) DO UPDATE SET
                generated_at = excluded.generated_at,
                payload_json = excluded.payload_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                report_id,
                report.case_id,
                report.simulation_id,
                report.generated_at,
                report.model_dump_json(),
            ),
        )
    return report.model_copy(deep=True)


def get_latest_replay_report(case_id: str) -> ReplayReportSnapshot | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT payload_json
            FROM replay_reports
            WHERE case_id = ?
            ORDER BY generated_at DESC, updated_at DESC
            LIMIT 1
            """,
            (case_id,),
        ).fetchone()

    if row is None:
        return None
    return ReplayReportSnapshot.model_validate_json(row["payload_json"])
