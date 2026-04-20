import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from apps.api.app.database import get_database_path, initialize_database


def test_database_initializes_trial_workflow_tables() -> None:
    initialize_database()

    with sqlite3.connect(get_database_path()) as connection:
        table_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

    assert {"trial_runs", "simulation_turns", "run_checkpoints"} <= table_names
