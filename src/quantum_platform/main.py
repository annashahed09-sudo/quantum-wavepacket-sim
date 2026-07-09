import json
import subprocess
from pathlib import Path

import psutil
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from quantum_platform.auth import create_access_token, get_current_user, hash_password, verify_password
from quantum_platform.config import settings
from quantum_platform.database import Base, engine, get_db
from quantum_platform.models import Project, SimulationRun, User
from quantum_platform.schemas import (
    LoginRequest,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    RegisterRequest,
    SimulationParams,
    SimulationRunResponse,
    TokenResponse,
    UserResponse,
)
from quantum_platform.services.simulation_service import run_simulation


app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def root() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.post("/api/auth/register", response_model=UserResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    existing_user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(email=payload.email, full_name=payload.full_name, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.email)
    return TokenResponse(access_token=token)


@app.get("/api/auth/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@app.post("/api/projects", response_model=ProjectResponse)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Project:
    project = Project(name=payload.name, description=payload.description, owner_id=user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@app.get("/api/projects", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[Project]:
    rows = db.execute(select(Project).where(Project.owner_id == user.id).order_by(Project.updated_at.desc())).scalars().all()
    return list(rows)


@app.patch("/api/projects/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Project:
    project = db.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description

    db.commit()
    db.refresh(project)
    return project


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    project = db.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"deleted": True}


@app.post("/api/simulations/run")
def run_simulation_route(
    payload: SimulationParams,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    if payload.project_id is not None:
        project = db.execute(
            select(Project).where(Project.id == payload.project_id, Project.owner_id == user.id)
        ).scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    params = payload.model_dump()
    result = run_simulation(params)

    run = SimulationRun(
        name=payload.name,
        project_id=payload.project_id,
        owner_id=user.id,
        steps=payload.steps,
        dt=payload.dt,
        grid_size=payload.grid_size,
        norm_final=result["stats"]["norm_final"],
        energy_final=result["stats"]["energy_final"],
        params_json=json.dumps(params),
        result_json=json.dumps(result),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    return {"run_id": run.id, "result": result}


@app.get("/api/simulations", response_model=list[SimulationRunResponse])
def list_simulations(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[SimulationRun]:
    rows = db.execute(
        select(SimulationRun).where(SimulationRun.owner_id == user.id).order_by(SimulationRun.created_at.desc())
    ).scalars().all()
    return list(rows)


@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    projects = db.execute(select(func.count(Project.id)).where(Project.owner_id == user.id)).scalar_one()
    simulations = db.execute(select(func.count(SimulationRun.id)).where(SimulationRun.owner_id == user.id)).scalar_one()
    latest_runs = db.execute(
        select(SimulationRun).where(SimulationRun.owner_id == user.id).order_by(SimulationRun.created_at.desc()).limit(5)
    ).scalars().all()

    return {
        "project_count": projects,
        "simulation_count": simulations,
        "latest_runs": [
            {
                "id": run.id,
                "name": run.name,
                "created_at": run.created_at.isoformat(),
                "norm_final": run.norm_final,
                "energy_final": run.energy_final,
            }
            for run in latest_runs
        ],
    }


@app.get("/api/system/status")
def system_status() -> dict:
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()

    gpu_name = None
    gpu_util = None
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,utilization.gpu", "--format=csv,noheader,nounits"],
            text=True,
            timeout=2,
        ).strip()
        if output:
            first = output.splitlines()[0]
            name, utilization = [value.strip() for value in first.split(",")]
            gpu_name = name
            gpu_util = float(utilization)
    except Exception:
        gpu_name = "Unavailable"

    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_available_gb": round(memory.available / 1024**3, 2),
        "gpu_name": gpu_name,
        "gpu_util_percent": gpu_util,
    }
