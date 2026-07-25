"""Simulation execution service.

Wires together the physics primitives (wavefunction, potentials) and the
split-operator solver to run a full TDSE simulation and return analysis
results.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from core.potentials import square_barrier
from core.wavefunction import gaussian_wavepacket
from solvers.split_operator import evolve, precompute_k


def _energy_expectation(
    psi: np.ndarray,
    k: np.ndarray,
    V: np.ndarray,
    dx: float,
    m: float = 1.0,
    hbar: float = 1.0,
) -> float:
    """Compute total energy expectation value :math:`\\langle E \\rangle`.

    Kinetic energy is evaluated in Fourier space and potential energy
    in position space.
    """
    psi_k = np.fft.fft(psi)
    kinetic_density_k = (hbar**2 * k**2 / (2.0 * m)) * np.abs(psi_k) ** 2 / len(psi)
    kinetic = float(np.sum(kinetic_density_k) * dx)
    potential = float(np.sum(np.abs(psi) ** 2 * V) * dx)
    return kinetic + potential


def run_simulation(params: dict[str, Any]) -> dict[str, Any]:
    """Run a full TDSE simulation from a parameter dictionary.

    Parameters
    ----------
    params : dict
        Must contain the keys:
            x_min, x_max, grid_size, x0, k0, sigma,
            barrier_height, barrier_width, barrier_center,
            steps, dt, sample_stride

    Returns
    -------
    dict
        With keys ``x``, ``frames``, and ``stats``.
    """
    # Build spatial grid
    x: np.ndarray = np.linspace(params["x_min"], params["x_max"], params["grid_size"])
    dx = float(x[1] - x[0])

    # Initial wavefunction and potential
    psi = gaussian_wavepacket(
        x,
        x0=params["x0"],
        k0=params["k0"],
        sigma=params["sigma"],
    )
    V = square_barrier(
        x,
        height=params["barrier_height"],
        width=params["barrier_width"],
        center=params["barrier_center"],
    )
    k = precompute_k(params["grid_size"], dx)

    frames: list[dict[str, Any]] = []
    dt = params["dt"]
    steps = params["steps"]
    stride = params["sample_stride"]

    for step in range(steps):
        psi = evolve(psi, V, x, dt, k)
        if step % stride == 0 or step == steps - 1:
            density = np.abs(psi) ** 2
            frames.append(
                {
                    "step": step,
                    "density": density.tolist(),
                    "norm": float(np.sum(density) * dx),
                    "peak_probability": float(np.max(density)),
                }
            )

    final_density = np.abs(psi) ** 2
    norm_final = float(np.sum(final_density) * dx)
    energy_final = _energy_expectation(psi, k, V, dx)

    # Momentum expectation value via the gradient (position-space) operator
    momentum_estimate = float(
        (np.sum(np.conj(psi) * (-1j * np.gradient(psi, dx))) * dx).real
    )

    stats: dict[str, Any] = {
        "norm_final": norm_final,
        "energy_final": energy_final,
        "momentum_estimate": momentum_estimate,
        "frames": len(frames),
    }

    return {"x": x.tolist(), "frames": frames, "stats": stats}
