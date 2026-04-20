from __future__ import annotations

from ..database import get_connection
from ..schemas.trial_workflow import RunCheckpointSnapshot


def save_checkpoint(checkpoint: RunCheckpointSnapshot) -> RunCheckpointSnapshot:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO run_checkpoints (
                checkpoint_id,
                trial_run_id,
                case_id,
                source_node_id,
                turn_index,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(checkpoint_id) DO UPDATE SET
                trial_run_id = excluded.trial_run_id,
                case_id = excluded.case_id,
                source_node_id = excluded.source_node_id,
                turn_index = excluded.turn_index,
                payload_json = excluded.payload_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                checkpoint.checkpoint_id,
                checkpoint.trial_run_id,
                checkpoint.case_id,
                checkpoint.source_node_id,
                checkpoint.turn_index,
                checkpoint.model_dump_json(),
            ),
        )
    return checkpoint.model_copy(deep=True)


def get_checkpoint(checkpoint_id: str) -> RunCheckpointSnapshot | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT payload_json
            FROM run_checkpoints
            WHERE checkpoint_id = ?
            """,
            (checkpoint_id,),
        ).fetchone()

    if row is None:
        return None
    return RunCheckpointSnapshot.model_validate_json(row["payload_json"])


def list_case_checkpoints(case_id: str) -> list[RunCheckpointSnapshot]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT payload_json
            FROM run_checkpoints
            WHERE case_id = ?
            ORDER BY turn_index DESC
            """,
            (case_id,),
        ).fetchall()

    return [RunCheckpointSnapshot.model_validate_json(row["payload_json"]) for row in rows]


def list_run_checkpoints(trial_run_id: str) -> list[RunCheckpointSnapshot]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT payload_json
            FROM run_checkpoints
            WHERE trial_run_id = ?
            ORDER BY turn_index DESC
            """,
            (trial_run_id,),
        ).fetchall()

    return [RunCheckpointSnapshot.model_validate_json(row["payload_json"]) for row in rows]
