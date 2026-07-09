from __future__ import annotations

import numpy as np

from backend.core.config import PotentialConfig


def build_potential(x: np.ndarray, cfg: PotentialConfig, mass: float = 1.0) -> np.ndarray:
    if cfg.kind == "free":
        return np.zeros_like(x, dtype=np.float64)

    if cfg.kind == "harmonic":
        return 0.5 * mass * (cfg.omega**2) * (x - cfg.center) ** 2

    potential = np.zeros_like(x, dtype=np.float64)
    potential[np.abs(x - cfg.center) < cfg.width / 2] = cfg.height
    return potential
