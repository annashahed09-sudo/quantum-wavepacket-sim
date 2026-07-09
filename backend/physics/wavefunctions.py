from __future__ import annotations

import numpy as np

from backend.core.config import GaussianWavePacketConfig


def gaussian_wavepacket(x: np.ndarray, cfg: GaussianWavePacketConfig) -> np.ndarray:
    norm = (1.0 / (cfg.sigma * np.sqrt(np.pi))) ** 0.5
    psi = norm * np.exp(-((x - cfg.x0) ** 2) / (2 * cfg.sigma**2)) * np.exp(1j * cfg.k0 * x)
    return psi.astype(np.complex128)
