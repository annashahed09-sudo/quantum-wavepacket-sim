from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Dict, Iterable, List

import numpy as np

from backend.analysis.diagnostics import Diagnostics, compute_diagnostics
from backend.core.config import Precision, SimulationConfig
from backend.fft.backends import FFTBackend, create_fft_backend
from backend.physics.potentials import build_potential
from backend.physics.wavefunctions import gaussian_wavepacket


_DTYPE_MAP = {
    Precision.FLOAT32: np.complex64,
    Precision.FLOAT64: np.complex128,
    Precision.COMPLEX64: np.complex64,
    Precision.COMPLEX128: np.complex128,
}


@dataclass
class SimulationFrame:
    step: int
    time: float
    probability_density: List[float]
    real_component: List[float]
    imaginary_component: List[float]
    phase: List[float]
    diagnostics: Dict[str, float]


@dataclass
class SimulationSummary:
    runtime_seconds: float
    backend: str
    frames_saved: int
    final_diagnostics: Dict[str, float]


class SplitOperatorSolver:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.backend: FFTBackend = create_fft_backend(config.backend)

        self.x = np.linspace(config.grid.x_min, config.grid.x_max, config.grid.points)
        self.dx = self.x[1] - self.x[0]
        self.k = 2 * np.pi * np.fft.fftfreq(config.grid.points, d=self.dx)

        self.potential = build_potential(self.x, config.potential, mass=config.particle.mass)
        self.psi = gaussian_wavepacket(self.x, config.initial_state)

        dtype = _DTYPE_MAP[config.precision]
        self.psi = self.psi.astype(dtype)
        self.initial_norm = float(np.sum(np.abs(self.psi) ** 2) * self.dx)

    def _choose_dt(self, current_dt: float, diagnostics: Diagnostics) -> float:
        if not self.config.time.adaptive_timestep:
            return current_dt

        dt_min = self.config.time.dt_min or current_dt
        dt_max = self.config.time.dt_max or current_dt
        if diagnostics.norm_error > 1e-4:
            return max(current_dt * 0.5, dt_min)
        if diagnostics.norm_error < 1e-8:
            return min(current_dt * 1.1, dt_max)
        return current_dt

    def _step(self, psi, dt: float):
        hbar = self.config.particle.hbar
        mass = self.config.particle.mass

        phase_half_v = self.backend.exp(-1j * self.potential * dt / (2 * hbar))
        psi = psi * phase_half_v

        psi_k = self.backend.fft(psi)
        kinetic_phase = self.backend.exp(-1j * (hbar * self.k**2) * dt / (2 * mass))
        psi_k = psi_k * kinetic_phase
        psi = self.backend.ifft(psi_k)

        psi = psi * phase_half_v
        return psi

    def run(self) -> tuple[list[SimulationFrame], SimulationSummary]:
        start = perf_counter()
        frames: list[SimulationFrame] = []
        dt = self.config.time.dt

        psi = self.backend.to_device(self.psi)
        for step in range(self.config.time.steps + 1):
            psi_host = self.backend.to_host(psi)
            diagnostics = compute_diagnostics(
                psi=psi_host,
                x=self.x,
                potential=self.potential,
                mass=self.config.particle.mass,
                hbar=self.config.particle.hbar,
                initial_norm=self.initial_norm,
            )

            if step % self.config.time.save_stride == 0:
                frames.append(
                    SimulationFrame(
                        step=step,
                        time=step * dt,
                        probability_density=np.abs(psi_host).tolist(),
                        real_component=np.real(psi_host).tolist(),
                        imaginary_component=np.imag(psi_host).tolist(),
                        phase=np.angle(psi_host).tolist(),
                        diagnostics={
                            "norm": diagnostics.norm,
                            "norm_error": diagnostics.norm_error,
                            "x_expectation": diagnostics.x_expectation,
                            "p_expectation": diagnostics.p_expectation,
                            "kinetic_energy": diagnostics.kinetic_energy,
                            "potential_energy": diagnostics.potential_energy,
                            "total_energy": diagnostics.total_energy,
                        },
                    )
                )

            if step < self.config.time.steps:
                psi = self._step(psi, dt)
                dt = self._choose_dt(dt, diagnostics)

        final = frames[-1].diagnostics if frames else {}
        summary = SimulationSummary(
            runtime_seconds=perf_counter() - start,
            backend=self.backend.name,
            frames_saved=len(frames),
            final_diagnostics=final,
        )
        return frames, summary

    async def stream(self) -> Iterable[SimulationFrame]:
        dt = self.config.time.dt
        psi = self.backend.to_device(self.psi)

        for step in range(self.config.time.steps + 1):
            psi_host = self.backend.to_host(psi)
            diagnostics = compute_diagnostics(
                psi=psi_host,
                x=self.x,
                potential=self.potential,
                mass=self.config.particle.mass,
                hbar=self.config.particle.hbar,
                initial_norm=self.initial_norm,
            )
            yield SimulationFrame(
                step=step,
                time=step * dt,
                probability_density=np.abs(psi_host).tolist(),
                real_component=np.real(psi_host).tolist(),
                imaginary_component=np.imag(psi_host).tolist(),
                phase=np.angle(psi_host).tolist(),
                diagnostics={
                    "norm": diagnostics.norm,
                    "norm_error": diagnostics.norm_error,
                    "x_expectation": diagnostics.x_expectation,
                    "p_expectation": diagnostics.p_expectation,
                    "kinetic_energy": diagnostics.kinetic_energy,
                    "potential_energy": diagnostics.potential_energy,
                    "total_energy": diagnostics.total_energy,
                },
            )
            if step < self.config.time.steps:
                psi = self._step(psi, dt)
                dt = self._choose_dt(dt, diagnostics)
