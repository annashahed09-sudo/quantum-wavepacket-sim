from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.core.config import SimulationConfig
from backend.database.store import SimulationStore
from backend.io.artifacts import save_frames_json
from backend.solvers.split_operator import SplitOperatorSolver


class JobManager:
    def __init__(self, store: SimulationStore | None = None):
        self.store = store or SimulationStore()
        self._tasks: dict[str, asyncio.Task] = {}

    async def create_simulation(self, config: SimulationConfig) -> str:
        run_id = str(uuid4())
        self.store.create_run(run_id=run_id, name=config.name, config=config.model_dump())
        return run_id

    async def run_simulation(self, run_id: str, config: SimulationConfig):
        if run_id in self._tasks and not self._tasks[run_id].done():
            raise ValueError(f"Run {run_id} is already active")

        task = asyncio.create_task(self._execute(run_id, config))
        self._tasks[run_id] = task
        return run_id

    async def _execute(self, run_id: str, config: SimulationConfig):
        self.store.update_status(run_id, "running")
        try:
            solver = SplitOperatorSolver(config)
            frames, summary = solver.run()
            payload = [asdict(frame) for frame in frames]
            frames_path = str(save_frames_json(run_id, payload))
            self.store.save_results(run_id, asdict(summary), frames_path)
        except Exception as exc:  # pragma: no cover - defensive
            self.store.mark_failed(run_id, str(exc))

    async def status(self, run_id: str) -> dict[str, Any] | None:
        row = self.store.get_run(run_id)
        if not row:
            return None
        return {
            "run_id": row["run_id"],
            "name": row["name"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    async def results(self, run_id: str) -> dict[str, Any] | None:
        row = self.store.get_run(run_id)
        if not row:
            return None

        response = {
            "run_id": row["run_id"],
            "status": row["status"],
            "summary": json.loads(row["summary_json"]) if row["summary_json"] else None,
            "frames": None,
        }

        if row.get("frames_path"):
            frame_path = Path(row["frames_path"])
            if frame_path.exists():
                response["frames"] = json.loads(frame_path.read_text())
        return response

    async def history(self, limit: int = 100):
        return self.store.list_runs(limit=limit)

    async def delete(self, run_id: str):
        row = self.store.get_run(run_id)
        if row and row.get("frames_path"):
            frame_path = Path(row["frames_path"])
            run_dir = frame_path.parent
            if run_dir.exists():
                for file in run_dir.glob("*"):
                    file.unlink(missing_ok=True)
                run_dir.rmdir()
        self.store.delete_run(run_id)


job_manager = JobManager()
