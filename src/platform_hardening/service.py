from __future__ import annotations

import time

import numpy as np

from core.potentials import square_barrier
from core.wavefunction import gaussian_wavepacket
from solvers.split_operator import evolve, precompute_k

from .authorization import can_override_limits, require_simulation_permission
from .errors import ConcurrencyError, TimeoutError, ValidationError
from .models import SimulationRequest, SimulationResult
from .policy import ServerLimits
from .quota import InMemoryQuotaManager
from .validation import requires_explicit_approval, validate_request


class SimulationService:
    """Server-side control plane around TDSE simulation execution."""

    def __init__(self, limits: ServerLimits | None = None, quota_manager: InMemoryQuotaManager | None = None):
        self._limits = limits or ServerLimits()
        self._quota_manager = quota_manager or InMemoryQuotaManager()
        self._active_jobs = 0

    @property
    def active_jobs(self) -> int:
        return self._active_jobs

    def run(self, request: SimulationRequest) -> SimulationResult:
        validate_request(request, self._limits)
        require_simulation_permission(request.role)

        if requires_explicit_approval(request, self._limits):
            if not request.approved_by_server and not can_override_limits(request.role):
                raise ValidationError("explicit server-side approval is required for this operation")

        if self._active_jobs >= self._limits.max_concurrent_jobs:
            raise ConcurrencyError("max concurrent jobs exceeded")

        self._quota_manager.consume(
            user_id=request.user_id,
            limits=self._limits,
            estimated_gpu_seconds=request.estimated_gpu_seconds,
        )

        self._active_jobs += 1
        try:
            return self._run_with_timeout(request)
        finally:
            self._active_jobs -= 1

    def _run_with_timeout(self, request: SimulationRequest) -> SimulationResult:
        x = np.linspace(request.x_min, request.x_max, request.grid_points)
        dx = x[1] - x[0]
        psi = gaussian_wavepacket(x, x0=request.x0, k0=request.k0, sigma=request.sigma)
        v = square_barrier(
            x,
            height=request.barrier_height,
            width=request.barrier_width,
            center=request.barrier_center,
        )
        k = precompute_k(request.grid_points, dx)

        started = time.monotonic()
        steps_executed = 0

        for _ in range(request.steps):
            elapsed = time.monotonic() - started
            if elapsed > self._limits.max_simulation_duration_seconds:
                raise TimeoutError("simulation exceeded max_simulation_duration_seconds")
            psi = evolve(psi, v, x, request.dt, k)
            steps_executed += 1

        elapsed = time.monotonic() - started
        final_norm = float(np.sum(np.abs(psi) ** 2) * dx)
        return SimulationResult(
            grid_points=request.grid_points,
            steps_executed=steps_executed,
            final_norm=final_norm,
            elapsed_seconds=elapsed,
        )
