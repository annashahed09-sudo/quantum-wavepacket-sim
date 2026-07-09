from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Diagnostics:
    norm: float
    norm_error: float
    x_expectation: float
    p_expectation: float
    kinetic_energy: float
    potential_energy: float
    total_energy: float


def _gradient_periodic(values: np.ndarray, dx: float) -> np.ndarray:
    return (np.roll(values, -1) - np.roll(values, 1)) / (2 * dx)


def compute_diagnostics(
    psi: np.ndarray,
    x: np.ndarray,
    potential: np.ndarray,
    mass: float,
    hbar: float,
    initial_norm: float,
) -> Diagnostics:
    density = np.abs(psi) ** 2
    dx = x[1] - x[0]

    norm = float(np.sum(density) * dx)
    x_expectation = float(np.sum(x * density) * dx)

    dpsi_dx = _gradient_periodic(psi, dx)
    p_density = np.conjugate(psi) * (-1j * hbar) * dpsi_dx
    p_expectation = float(np.real(np.sum(p_density) * dx))

    kinetic_density = (hbar**2 / (2 * mass)) * np.abs(dpsi_dx) ** 2
    kinetic_energy = float(np.sum(kinetic_density) * dx)
    potential_energy = float(np.sum(density * potential) * dx)

    return Diagnostics(
        norm=norm,
        norm_error=abs(norm - initial_norm),
        x_expectation=x_expectation,
        p_expectation=p_expectation,
        kinetic_energy=kinetic_energy,
        potential_energy=potential_energy,
        total_energy=kinetic_energy + potential_energy,
    )
