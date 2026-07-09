from __future__ import annotations

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from backend.api.schemas import CompareRequest, CreateSimulationRequest, ExportRequest, RunSimulationRequest
from backend.core.config import SimulationConfig
from backend.io.artifacts import compare_runs, export_csv, export_hdf5, export_npy, resolve_run_dir_from_frames_path
from backend.jobs.manager import job_manager
from backend.solvers.split_operator import SplitOperatorSolver

app = FastAPI(title="Quantum Dynamics Platform", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/simulation/create")
async def create_simulation(payload: CreateSimulationRequest):
    run_id = await job_manager.create_simulation(payload.config)
    return {"run_id": run_id}


@app.post("/simulation/run")
async def run_simulation(payload: RunSimulationRequest):
    await job_manager.run_simulation(payload.run_id, payload.config)
    return {"run_id": payload.run_id, "status": "queued"}


@app.get("/simulation/status/{run_id}")
async def get_status(run_id: str):
    status = await job_manager.status(run_id)
    if not status:
        raise HTTPException(status_code=404, detail="run not found")
    return status


@app.get("/simulation/results/{run_id}")
async def get_results(run_id: str):
    results = await job_manager.results(run_id)
    if not results:
        raise HTTPException(status_code=404, detail="run not found")
    return results


@app.get("/simulation/history")
async def get_history(limit: int = 100):
    return {"runs": await job_manager.history(limit=limit)}


@app.delete("/simulation/{run_id}")
async def delete_run(run_id: str):
    status = await job_manager.status(run_id)
    if not status:
        raise HTTPException(status_code=404, detail="run not found")
    await job_manager.delete(run_id)
    return {"deleted": run_id}


@app.post("/simulation/compare")
async def compare(request: CompareRequest):
    a = await job_manager.results(request.run_a)
    b = await job_manager.results(request.run_b)
    if not a or not b:
        raise HTTPException(status_code=404, detail="one or both runs not found")
    if not a.get("frames") or not b.get("frames"):
        raise HTTPException(status_code=400, detail="completed frames required for comparison")
    return compare_runs(a["frames"], b["frames"])


@app.post("/export")
async def export(request: ExportRequest):
    results = await job_manager.results(request.run_id)
    if not results:
        raise HTTPException(status_code=404, detail="run not found")
    frames = results.get("frames")
    if not results.get("frames"):
        raise HTTPException(status_code=400, detail="no frames available")
    if not results.get("frames_path"):
        raise HTTPException(status_code=400, detail="frame artifact path unavailable")
    run_dir = resolve_run_dir_from_frames_path(results["frames_path"])

    outputs: dict[str, str] = {}
    for fmt in request.formats:
        if fmt == "csv":
            outputs[fmt] = str(export_csv(run_dir, frames))
        elif fmt == "npy":
            outputs[fmt] = str(export_npy(run_dir, frames))
        elif fmt == "hdf5":
            outputs[fmt] = str(export_hdf5(run_dir, frames))
        elif fmt == "json":
            path = run_dir / "frames.json"
            outputs[fmt] = str(path)
        else:
            raise HTTPException(status_code=400, detail=f"unsupported export format: {fmt}")
    return {"exports": outputs}


@app.get("/gpu")
def gpu_info():
    info = {"available": False, "backend": None}
    try:
        import cupy as cp  # type: ignore

        info["available"] = True
        info["backend"] = "cupy"
        info["device_count"] = cp.cuda.runtime.getDeviceCount()
    except Exception:
        pass
    return info


@app.get("/performance")
async def performance():
    history = await job_manager.history(limit=100)
    completed = [run for run in history if run["status"] == "completed"]
    return {
        "completed_runs": len(completed),
        "queued_or_running": len([run for run in history if run["status"] in {"queued", "running"}]),
    }


@app.websocket("/live")
async def live(websocket: WebSocket):
    await websocket.accept()
    try:
        payload = await websocket.receive_json()
        config = SimulationConfig.model_validate(payload.get("config", {}))
        solver = SplitOperatorSolver(config)
        async for frame in solver.stream():
            await websocket.send_json(
                {
                    "step": frame.step,
                    "time": frame.time,
                    "probability_density": frame.probability_density,
                    "real_component": frame.real_component,
                    "imaginary_component": frame.imaginary_component,
                    "phase": frame.phase,
                    "diagnostics": frame.diagnostics,
                }
            )
    except WebSocketDisconnect:
        return
    finally:
        await websocket.close()
