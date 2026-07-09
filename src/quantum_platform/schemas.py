from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SimulationParams(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    project_id: int | None = None
    x_min: float = -50.0
    x_max: float = 50.0
    grid_size: int = Field(default=1024, ge=128, le=8192)
    dt: float = Field(default=0.01, gt=0)
    steps: int = Field(default=300, ge=1, le=10000)
    sample_stride: int = Field(default=5, ge=1, le=500)
    x0: float = -15.0
    k0: float = 6.0
    sigma: float = Field(default=1.5, gt=0)
    barrier_height: float = 1.0
    barrier_width: float = Field(default=3.0, gt=0)
    barrier_center: float = 0.0


class SimulationResult(BaseModel):
    x: list[float]
    frames: list[dict]
    stats: dict


class SimulationRunResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    project_id: int | None
    steps: int
    dt: float
    grid_size: int
    norm_final: float
    energy_final: float

    class Config:
        from_attributes = True
