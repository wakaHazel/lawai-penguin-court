from __future__ import annotations

import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


_ROOT_DIR = Path(__file__).resolve().parents[3]
_DEFAULT_RUNTIME_DATA_DIR = _ROOT_DIR / "data"
_DEFAULT_STATIC_ASSETS_DIR = _ROOT_DIR / "data"


def get_workspace_root() -> Path:
    return _ROOT_DIR


def get_runtime_data_dir() -> Path:
    configured_dir = os.getenv("PENGUIN_RUNTIME_DATA_DIR", "").strip()
    return Path(configured_dir) if configured_dir else _DEFAULT_RUNTIME_DATA_DIR


def get_static_assets_dir() -> Path:
    configured_dir = os.getenv("PENGUIN_STATIC_ASSETS_DIR", "").strip()
    return Path(configured_dir) if configured_dir else _DEFAULT_STATIC_ASSETS_DIR


def get_generated_cg_dir() -> Path:
    return get_runtime_data_dir() / "generated-cg"


def get_static_cg_library_dir() -> Path:
    return get_static_assets_dir() / "cg-library"


def get_database_path() -> Path:
    return get_runtime_data_dir() / "penguin_court.db"


def initialize_database() -> None:
    runtime_data_dir = get_runtime_data_dir()
    runtime_data_dir.mkdir(parents=True, exist_ok=True)
    get_generated_cg_dir().mkdir(parents=True, exist_ok=True)
    database_path = get_database_path()

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA journal_mode=WAL;")
        connection.execute("PRAGMA foreign_keys=ON;")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                case_type TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS simulations (
                simulation_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                current_stage TEXT NOT NULL,
                turn_index INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(case_id) REFERENCES cases(case_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS replay_reports (
                report_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                simulation_id TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(case_id) REFERENCES cases(case_id) ON DELETE CASCADE,
                FOREIGN KEY(simulation_id) REFERENCES simulations(simulation_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS opponent_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                simulation_id TEXT NOT NULL,
                current_stage TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(case_id) REFERENCES cases(case_id) ON DELETE CASCADE,
                FOREIGN KEY(simulation_id) REFERENCES simulations(simulation_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS win_rate_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                simulation_id TEXT NOT NULL,
                current_stage TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(case_id) REFERENCES cases(case_id) ON DELETE CASCADE,
                FOREIGN KEY(simulation_id) REFERENCES simulations(simulation_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS trial_runs (
                trial_run_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                current_node_id TEXT NOT NULL,
                current_stage TEXT NOT NULL,
                turn_index INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(case_id) REFERENCES cases(case_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS simulation_turns (
                turn_id TEXT PRIMARY KEY,
                trial_run_id TEXT NOT NULL,
                case_id TEXT NOT NULL,
                node_id TEXT NOT NULL,
                current_stage TEXT NOT NULL,
                turn_index INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(case_id) REFERENCES cases(case_id) ON DELETE CASCADE,
                FOREIGN KEY(trial_run_id) REFERENCES trial_runs(trial_run_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS run_checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                trial_run_id TEXT NOT NULL,
                case_id TEXT NOT NULL,
                source_node_id TEXT NOT NULL,
                turn_index INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(case_id) REFERENCES cases(case_id) ON DELETE CASCADE,
                FOREIGN KEY(trial_run_id) REFERENCES trial_runs(trial_run_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_cases_updated_at
            ON cases(updated_at DESC)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_simulations_case_updated
            ON simulations(case_id, updated_at DESC)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_replay_reports_case_generated
            ON replay_reports(case_id, generated_at DESC)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_opponent_snapshots_case_updated
            ON opponent_snapshots(case_id, updated_at DESC)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_win_rate_snapshots_case_updated
            ON win_rate_snapshots(case_id, updated_at DESC)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_trial_runs_case_updated
            ON trial_runs(case_id, updated_at DESC)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_simulation_turns_case_turn
            ON simulation_turns(case_id, turn_index DESC)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_run_checkpoints_case_turn
            ON run_checkpoints(case_id, turn_index DESC)
            """
        )
        connection.commit()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    initialize_database()
    connection = sqlite3.connect(get_database_path())
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys=ON;")
        yield connection
        connection.commit()
    finally:
        connection.close()
