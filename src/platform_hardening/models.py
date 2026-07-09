from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    GUEST = "guest"
    USER = "user"
    RESEARCHER = "researcher"
    ADMINISTRATOR = "administrator"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True)
class SimulationRequest:
    user_id: str
    role: Role
    grid_points: int
    steps: int
    dt: float
    x_min: float
    x_max: float
    x0: float
    k0: float
    sigma: float
    barrier_height: float
    barrier_width: float
    barrier_center: float = 0.0
    requires_gpu: bool = False
    estimated_gpu_seconds: float = 0.0
    approved_by_server: bool = False


@dataclass(frozen=True)
class SimulationResult:
    grid_points: int
    steps_executed: int
    final_norm: float
    elapsed_seconds: float
