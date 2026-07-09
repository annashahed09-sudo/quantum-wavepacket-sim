from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class SimulationStore:
    def __init__(self, db_path: str = "backend/database/simulations.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS simulation_runs (
                    run_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    summary_json TEXT,
                    frames_path TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def create_run(self, run_id: str, name: str, config: dict[str, Any]):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO simulation_runs(run_id, name, status, config_json) VALUES (?, ?, ?, ?)",
                (run_id, name, "queued", json.dumps(config)),
            )

    def update_status(self, run_id: str, status: str):
        with self._connect() as conn:
            conn.execute(
                "UPDATE simulation_runs SET status=?, updated_at=CURRENT_TIMESTAMP WHERE run_id=?",
                (status, run_id),
            )

    def save_results(self, run_id: str, summary: dict[str, Any], frames_path: str):
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE simulation_runs
                SET status=?, summary_json=?, frames_path=?, updated_at=CURRENT_TIMESTAMP
                WHERE run_id=?
                """,
                ("completed", json.dumps(summary), frames_path, run_id),
            )

    def mark_failed(self, run_id: str, reason: str):
        with self._connect() as conn:
            conn.execute(
                "UPDATE simulation_runs SET status=?, summary_json=?, updated_at=CURRENT_TIMESTAMP WHERE run_id=?",
                ("failed", json.dumps({"error": reason}), run_id),
            )

    def get_run(self, run_id: str):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM simulation_runs WHERE run_id=?", (run_id,)).fetchone()
            return dict(row) if row else None

    def list_runs(self, limit: int = 100):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT run_id, name, status, created_at, updated_at FROM simulation_runs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_run(self, run_id: str):
        with self._connect() as conn:
            conn.execute("DELETE FROM simulation_runs WHERE run_id=?", (run_id,))
