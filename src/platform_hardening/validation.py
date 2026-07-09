from __future__ import annotations

import math

from .errors import ValidationError
from .models import SimulationRequest
from .policy import ServerLimits


def _assert_finite(value: float, field: str) -> None:
    if not math.isfinite(value):
        raise ValidationError(f"{field} must be a finite number")


def _estimate_job_memory_bytes(grid_points: int) -> int:
    # Complex128 wavefunction plus potential and FFT buffers.
    return grid_points * (16 * 3)


def validate_request(request: SimulationRequest, limits: ServerLimits) -> SimulationRequest:
    if not request.user_id or len(request.user_id) > 128:
        raise ValidationError("user_id is required and must be <=128 characters")

    if request.grid_points < 64:
        raise ValidationError("grid_points must be at least 64")

    if request.grid_points > limits.max_fft_grid_size:
        raise ValidationError("grid_points exceeds max_fft_grid_size")

    if request.steps < 1:
        raise ValidationError("steps must be at least 1")

    if request.steps > limits.max_simulation_steps:
        raise ValidationError("steps exceeds max_simulation_steps")

    for field_name in (
        "dt",
        "x_min",
        "x_max",
        "x0",
        "k0",
        "sigma",
        "barrier_height",
        "barrier_width",
        "barrier_center",
        "estimated_gpu_seconds",
    ):
        _assert_finite(getattr(request, field_name), field_name)

    if request.dt <= 0:
        raise ValidationError("dt must be > 0")

    if request.sigma <= 0:
        raise ValidationError("sigma must be > 0")

    if request.x_max <= request.x_min:
        raise ValidationError("x_max must be greater than x_min")

    if request.barrier_width <= 0:
        raise ValidationError("barrier_width must be > 0")

    if request.barrier_height < 0:
        raise ValidationError("barrier_height must be >= 0")

    if request.estimated_gpu_seconds < 0:
        raise ValidationError("estimated_gpu_seconds must be >= 0")

    if _estimate_job_memory_bytes(request.grid_points) > limits.max_memory_bytes_per_job:
        raise ValidationError("estimated job memory exceeds max_memory_bytes_per_job")

    return request


def requires_explicit_approval(request: SimulationRequest, limits: ServerLimits) -> bool:
    return (
        request.steps > limits.expensive_steps_threshold
        or request.grid_points > limits.expensive_grid_threshold
        or request.requires_gpu
    )
