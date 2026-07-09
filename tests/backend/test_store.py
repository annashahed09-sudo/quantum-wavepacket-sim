from pathlib import Path

from backend.database.store import SimulationStore


def test_store_create_and_update(tmp_path: Path):
    db = tmp_path / "sim.db"
    store = SimulationStore(str(db))

    store.create_run("run-1", "test", {"a": 1})
    store.update_status("run-1", "running")
    row = store.get_run("run-1")

    assert row is not None
    assert row["status"] == "running"
