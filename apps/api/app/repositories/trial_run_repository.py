from __future__ import annotations

from ..database import get_connection
from ..schemas.trial_workflow import TrialRunSnapshot
from ..schemas.turn import SimulationSnapshot


def save_trial_run(run: TrialRunSnapshot) -> TrialRunSnapshot:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO trial_runs (
                trial_run_id,
                case_id,
                current_node_id,
                current_stage,
                turn_index,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(trial_run_id) DO UPDATE SET
                current_node_id = excluded.current_node_id,
                current_stage = excluded.current_stage,
                turn_index = excluded.turn_index,
                payload_json = excluded.payload_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                run.trial_run_id,
                run.case_id,
                run.current_node_id,
                run.current_stage.value,
                run.turn_index,
                run.model_dump_json(),
            ),
        )
    return run.model_copy(deep=True)


def get_trial_run(trial_run_id: str) -> TrialRunSnapshot | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT payload_json FROM trial_runs WHERE trial_run_id = ?",
            (trial_run_id,),
        ).fetchone()

    if row is None:
        return None
    return TrialRunSnapshot.model_validate_json(row["payload_json"])


def get_latest_trial_run(case_id: str) -> TrialRunSnapshot | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT payload_json
            FROM trial_runs
            WHERE case_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (case_id,),
        ).fetchone()

    if row is None:
        return None
    return TrialRunSnapshot.model_validate_json(row["payload_json"])


def append_simulation_turn(turn: SimulationSnapshot) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO simulation_turns (
                turn_id,
                trial_run_id,
                case_id,
                node_id,
                current_stage,
                turn_index,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"{turn.simulation_id}:{turn.turn_index}",
                turn.simulation_id,
                turn.case_id,
                turn.node_id,
                turn.current_stage.value,
                turn.turn_index,
                turn.model_dump_json(),
            ),
        )


def get_latest_turn_for_run(trial_run_id: str) -> SimulationSnapshot | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT payload_json
            FROM simulation_turns
            WHERE trial_run_id = ?
            ORDER BY turn_index DESC
            LIMIT 1
            """,
            (trial_run_id,),
        ).fetchone()

    if row is None:
        return None
    return SimulationSnapshot.model_validate_json(row["payload_json"])


def list_simulation_turns(case_id: str) -> list[SimulationSnapshot]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT payload_json
            FROM simulation_turns
            WHERE case_id = ?
            ORDER BY turn_index ASC
            """,
            (case_id,),
        ).fetchall()

    return [SimulationSnapshot.model_validate_json(row["payload_json"]) for row in rows]


def list_simulation_turns_for_run(trial_run_id: str) -> list[SimulationSnapshot]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT payload_json
            FROM simulation_turns
            WHERE trial_run_id = ?
            ORDER BY turn_index ASC
            """,
            (trial_run_id,),
        ).fetchall()

    return [SimulationSnapshot.model_validate_json(row["payload_json"]) for row in rows]
