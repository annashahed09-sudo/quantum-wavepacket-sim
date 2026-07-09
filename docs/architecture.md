# Quantum Dynamics Platform Architecture

## v1 Scope
- 1D TDSE via split-operator Fourier method
- CPU-first execution with optional CuPy/PyFFTW acceleration
- FastAPI simulation lifecycle endpoints and WebSocket streaming
- SQLite run persistence and artifact export (JSON/CSV/NPY/HDF5)
- Next.js dashboard for launch and live visualization

## Backend Modules
- `backend/core`: typed simulation configuration and validation
- `backend/physics`: wavefunction and potential model builders
- `backend/fft`: backend abstraction for NumPy/PyFFTW/CuPy FFT engines
- `backend/solvers`: split-operator simulation loop and streaming frames
- `backend/analysis`: norm, expectation values, and energy diagnostics
- `backend/jobs`: async job orchestration and run lifecycle state
- `backend/database`: SQLite persistence schema and data access
- `backend/io`: artifact storage, export, and run comparison utilities
- `backend/api`: REST and WebSocket interfaces

## Scaling Path
- Keep API stable while replacing internals with distributed workers
- Add PostgreSQL migration for production metadata persistence
- Extend FFT backend contract for ROCm/OpenCL/Metal and distributed FFT
- Add queue backends (Redis/RQ/Celery) while preserving job manager interface
