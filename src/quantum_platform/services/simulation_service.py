import numpy as np

from core.potentials import square_barrier
from core.wavefunction import gaussian_wavepacket
from solvers.split_operator import evolve, precompute_k


def _energy_expectation(psi: np.ndarray, k: np.ndarray, V: np.ndarray, dx: float, m: float = 1.0, hbar: float = 1.0) -> float:
    psi_k = np.fft.fft(psi)
    kinetic_density_k = (hbar**2 * k**2 / (2 * m)) * np.abs(psi_k) ** 2 / len(psi)
    kinetic = float(np.sum(kinetic_density_k) * dx)
    potential = float(np.sum(np.abs(psi) ** 2 * V) * dx)
    return kinetic + potential


def run_simulation(params: dict) -> dict:
    x = np.linspace(params["x_min"], params["x_max"], params["grid_size"])
    dx = x[1] - x[0]

    psi = gaussian_wavepacket(x, x0=params["x0"], k0=params["k0"], sigma=params["sigma"])
    V = square_barrier(x, height=params["barrier_height"], width=params["barrier_width"], center=params["barrier_center"])
    k = precompute_k(params["grid_size"], dx)

    frames: list[dict] = []

    for step in range(params["steps"]):
        psi = evolve(psi, V, x, params["dt"], k)
        if step % params["sample_stride"] == 0 or step == params["steps"] - 1:
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

    stats = {
        "norm_final": norm_final,
        "energy_final": energy_final,
        "momentum_estimate": float(np.sum(np.conj(psi) * (-1j * np.gradient(psi, dx))) * dx).real,
        "frames": len(frames),
    }

    return {"x": x.tolist(), "frames": frames, "stats": stats}
