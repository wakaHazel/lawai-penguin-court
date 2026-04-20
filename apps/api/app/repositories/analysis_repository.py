from __future__ import annotations

from ..database import get_connection
from ..schemas.analysis import OpponentBehaviorSnapshot, WinRateAnalysisSnapshot


def save_opponent_snapshot(snapshot: OpponentBehaviorSnapshot) -> OpponentBehaviorSnapshot:
    snapshot_id = f"{snapshot.case_id}:{snapshot.simulation_id}"
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO opponent_snapshots (
                snapshot_id,
                case_id,
                simulation_id,
                current_stage,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(snapshot_id) DO UPDATE SET
                current_stage = excluded.current_stage,
                payload_json = excluded.payload_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                snapshot_id,
                snapshot.case_id,
                snapshot.simulation_id,
                snapshot.current_stage.value,
                snapshot.model_dump_json(),
            ),
        )
    return snapshot.model_copy(deep=True)


def get_latest_opponent_snapshot(case_id: str) -> OpponentBehaviorSnapshot | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT payload_json
            FROM opponent_snapshots
            WHERE case_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (case_id,),
        ).fetchone()

    if row is None:
        return None
    return OpponentBehaviorSnapshot.model_validate_json(row["payload_json"])


def save_win_rate_snapshot(snapshot: WinRateAnalysisSnapshot) -> WinRateAnalysisSnapshot:
    snapshot_id = f"{snapshot.case_id}:{snapshot.simulation_id}"
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO win_rate_snapshots (
                snapshot_id,
                case_id,
                simulation_id,
                current_stage,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(snapshot_id) DO UPDATE SET
                current_stage = excluded.current_stage,
                payload_json = excluded.payload_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                snapshot_id,
                snapshot.case_id,
                snapshot.simulation_id,
                snapshot.current_stage.value,
                snapshot.model_dump_json(),
            ),
        )
    return snapshot.model_copy(deep=True)


def get_latest_win_rate_snapshot(case_id: str) -> WinRateAnalysisSnapshot | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT payload_json
            FROM win_rate_snapshots
            WHERE case_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (case_id,),
        ).fetchone()

    if row is None:
        return None
    return WinRateAnalysisSnapshot.model_validate_json(row["payload_json"])
