from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.core.config import SimulationConfig


class CreateSimulationRequest(BaseModel):
    config: SimulationConfig = Field(default_factory=SimulationConfig)


class CreateSimulationResponse(BaseModel):
    run_id: str


class RunSimulationRequest(BaseModel):
    run_id: str
    config: SimulationConfig


class ExportRequest(BaseModel):
    run_id: str
    formats: list[str] = Field(default_factory=lambda: ["json", "csv"])


class CompareRequest(BaseModel):
    run_a: str
    run_b: str


class GenericResponse(BaseModel):
    data: Any
