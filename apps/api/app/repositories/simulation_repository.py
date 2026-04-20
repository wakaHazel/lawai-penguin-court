from __future__ import annotations

from ..database import get_connection
from ..schemas.turn import SimulationSnapshot


def save_simulation(snapshot: SimulationSnapshot) -> SimulationSnapshot:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO simulations (
                simulation_id,
                case_id,
                current_stage,
                turn_index,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(simulation_id) DO UPDATE SET
                case_id = excluded.case_id,
                current_stage = excluded.current_stage,
                turn_index = excluded.turn_index,
                payload_json = excluded.payload_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                snapshot.simulation_id,
                snapshot.case_id,
                snapshot.current_stage.value,
                snapshot.turn_index,
                snapshot.model_dump_json(),
            ),
        )
    return snapshot.model_copy(deep=True)


def get_simulation(simulation_id: str) -> SimulationSnapshot | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT payload_json
            FROM simulations
            WHERE simulation_id = ?
            """,
            (simulation_id,),
        ).fetchone()

    if row is None:
        return None
    return SimulationSnapshot.model_validate_json(row["payload_json"])


def get_latest_simulation(case_id: str) -> SimulationSnapshot | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT payload_json
            FROM simulations
            WHERE case_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (case_id,),
        ).fetchone()

    if row is None:
        return None
    return SimulationSnapshot.model_validate_json(row["payload_json"])
