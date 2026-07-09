# Quantum Dynamics Platform

Production-oriented computational platform for solving the 1D time-dependent Schrödinger equation (TDSE) with a split-operator Fourier solver, API-first execution, and interactive web visualization.

## Implemented Foundation

- Typed simulation configuration and validation (Pydantic)
- Split-operator solver with backend abstraction (NumPy, optional CuPy/PyFFTW)
- Diagnostics: norm, norm error, expectation values, kinetic/potential/total energy
- Async simulation job orchestration and lifecycle tracking
- SQLite persistence for simulation runs
- FastAPI endpoints and `/live` WebSocket streaming
- Artifact export to JSON, CSV, NPY, and HDF5
- Run comparison utilities
- Next.js frontend scaffold with landing page and dashboard
- CI workflow and Docker/Compose deployment scaffolding

## Repository Layout

```text
backend/
  api/
  core/
  physics/
  solvers/
  fft/
  analysis/
  io/
  database/
  jobs/
frontend/
  src/components/
  src/pages/
  src/services/
tests/
docs/
docker/
```

## API Endpoints

- `POST /simulation/create`
- `POST /simulation/run`
- `GET /simulation/status/{run_id}`
- `GET /simulation/results/{run_id}`
- `GET /simulation/history`
- `DELETE /simulation/{run_id}`
- `POST /simulation/compare`
- `POST /export`
- `GET /gpu`
- `GET /performance`
- `WS /live`

## Backend Quick Start

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

## Frontend Quick Start

```bash
cd frontend
npm install
npm run dev
```

## Tests

```bash
pytest -q
```

## Notes

- CuPy and PyFFTW are optional and auto-detected when installed.
- v1 targets 1D simulations; APIs are structured for future 2D/3D and distributed execution.
