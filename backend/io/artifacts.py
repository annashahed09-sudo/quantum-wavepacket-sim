from __future__ import annotations

import csv
import json
from uuid import UUID
from pathlib import Path
from typing import Any

import h5py
import numpy as np


ARTIFACT_ROOT = Path("backend/io/artifacts")


def _validate_under_root(path: Path) -> Path:
    root_resolved = ARTIFACT_ROOT.resolve()
    if root_resolved not in path.parents and path != root_resolved:
        raise ValueError("invalid artifact path")
    return path


def ensure_run_dir_from_id(run_id: str) -> Path:
    run_uuid = UUID(run_id)
    run_dir = _validate_under_root((ARTIFACT_ROOT / run_uuid.hex).resolve())
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def resolve_run_dir_from_frames_path(frames_path: str) -> Path:
    run_dir = _validate_under_root(Path(frames_path).resolve().parent)
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def save_frames_json(run_id: str, frames: list[dict[str, Any]]) -> Path:
    run_dir = ensure_run_dir_from_id(run_id)
    output = run_dir / "frames.json"
    output.write_text(json.dumps(frames))
    return output


def export_csv(run_dir: Path, frames: list[dict[str, Any]]) -> Path:
    output = run_dir / "diagnostics.csv"
    with output.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["step", "time", "norm", "norm_error", "x_expectation", "p_expectation", "total_energy"],
        )
        writer.writeheader()
        for frame in frames:
            d = frame["diagnostics"]
            writer.writerow(
                {
                    "step": frame["step"],
                    "time": frame["time"],
                    "norm": d["norm"],
                    "norm_error": d["norm_error"],
                    "x_expectation": d["x_expectation"],
                    "p_expectation": d["p_expectation"],
                    "total_energy": d["total_energy"],
                }
            )
    return output


def export_npy(run_dir: Path, frames: list[dict[str, Any]]) -> Path:
    output = run_dir / "probability_density.npy"
    density = np.array([frame["probability_density"] for frame in frames])
    np.save(output, density)
    return output


def export_hdf5(run_dir: Path, frames: list[dict[str, Any]]) -> Path:
    output = run_dir / "simulation.h5"
    density = np.array([frame["probability_density"] for frame in frames])
    phase = np.array([frame["phase"] for frame in frames])

    with h5py.File(output, "w") as handle:
        handle.create_dataset("probability_density", data=density)
        handle.create_dataset("phase", data=phase)
    return output


def compare_runs(run_a: list[dict[str, Any]], run_b: list[dict[str, Any]]) -> dict[str, float]:
    min_len = min(len(run_a), len(run_b))
    if min_len == 0:
        return {"l2_probability_gap": 0.0, "energy_drift_gap": 0.0}

    density_a = np.array([run_a[i]["probability_density"] for i in range(min_len)])
    density_b = np.array([run_b[i]["probability_density"] for i in range(min_len)])
    l2_gap = float(np.linalg.norm(density_a - density_b) / np.sqrt(density_a.size))

    e_a = np.array([run_a[i]["diagnostics"]["total_energy"] for i in range(min_len)])
    e_b = np.array([run_b[i]["diagnostics"]["total_energy"] for i in range(min_len)])
    energy_gap = float(np.mean(np.abs(e_a - e_b)))

    return {"l2_probability_gap": l2_gap, "energy_drift_gap": energy_gap}
