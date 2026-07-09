from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class Precision(str, Enum):
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    COMPLEX64 = "complex64"
    COMPLEX128 = "complex128"


class BackendKind(str, Enum):
    AUTO = "auto"
    NUMPY = "numpy"
    PYFFTW = "pyfftw"
    CUPY = "cupy"


class BoundaryCondition(str, Enum):
    PERIODIC = "periodic"
    FIXED = "fixed"
    ABSORBING = "absorbing"


class GridConfig(BaseModel):
    dimension: Literal[1] = 1
    points: int = Field(default=1024, ge=64)
    x_min: float = -50.0
    x_max: float = 50.0
    boundary: BoundaryCondition = BoundaryCondition.PERIODIC

    @property
    def dx(self) -> float:
        return (self.x_max - self.x_min) / (self.points - 1)

    @field_validator("x_max")
    @classmethod
    def _validate_range(cls, value: float, info):
        x_min = info.data.get("x_min")
        if x_min is not None and value <= x_min:
            raise ValueError("x_max must be greater than x_min")
        return value


class TimeConfig(BaseModel):
    dt: float = Field(default=0.01, gt=0)
    total_time: float = Field(default=5.0, gt=0)
    save_stride: int = Field(default=10, ge=1)
    adaptive_timestep: bool = False
    dt_min: Optional[float] = Field(default=None, gt=0)
    dt_max: Optional[float] = Field(default=None, gt=0)

    @property
    def steps(self) -> int:
        return int(round(self.total_time / self.dt))

    @model_validator(mode="after")
    def _validate_adaptive(self):
        if self.adaptive_timestep and (self.dt_min is None or self.dt_max is None):
            raise ValueError("dt_min and dt_max are required when adaptive_timestep is enabled")
        if self.dt_min is not None and self.dt_max is not None and self.dt_min > self.dt_max:
            raise ValueError("dt_min must not exceed dt_max")
        return self


class ParticleConfig(BaseModel):
    mass: float = Field(default=1.0, gt=0)
    hbar: float = Field(default=1.0, gt=0)


class GaussianWavePacketConfig(BaseModel):
    x0: float = -15.0
    k0: float = 6.0
    sigma: float = Field(default=1.5, gt=0)


class PotentialConfig(BaseModel):
    kind: Literal["square_barrier", "free", "harmonic"] = "square_barrier"
    height: float = 1.0
    width: float = Field(default=3.0, gt=0)
    center: float = 0.0
    omega: float = Field(default=0.5, gt=0)


class SimulationConfig(BaseModel):
    name: str = Field(default="tdse-simulation", min_length=1, max_length=128)
    backend: BackendKind = BackendKind.AUTO
    precision: Precision = Precision.COMPLEX128
    grid: GridConfig = Field(default_factory=GridConfig)
    time: TimeConfig = Field(default_factory=TimeConfig)
    particle: ParticleConfig = Field(default_factory=ParticleConfig)
    initial_state: GaussianWavePacketConfig = Field(default_factory=GaussianWavePacketConfig)
    potential: PotentialConfig = Field(default_factory=PotentialConfig)
