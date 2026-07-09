# Quantum Wavepacket Platform

Production-oriented quantum simulation platform with:

- **Scientific simulation engine** (TDSE split-operator Fourier solver)
- **FastAPI backend** with JWT authentication
- **Persistent project and simulation storage** (SQLite via SQLAlchemy)
- **Interactive desktop-first UI** with glassmorphism styling and live visualization canvas
- **System and GPU monitor endpoint**
- **Automated tests + CI workflow + Docker runtime**

## Architecture

```text
src/
├── core/                          # physics primitives (wavefunction + potentials)
├── solvers/                       # split-operator numerical solver
├── main.py                        # uvicorn entrypoint
└── quantum_platform/
    ├── auth.py                    # password hashing + JWT handling
    ├── config.py                  # environment configuration
    ├── database.py                # SQLAlchemy engine/session
    ├── models.py                  # ORM models (users, projects, runs)
    ├── schemas.py                 # API contracts
    ├── main.py                    # FastAPI app + API routes
    ├── services/
    │   └── simulation_service.py  # simulation execution service
    └── static/
        ├── index.html             # desktop app shell
        ├── styles.css             # Apple-inspired glass UI styles
        └── app.js                 # frontend behavior and API integration
```

## API Surface

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/projects`
- `GET /api/projects`
- `PATCH /api/projects/{project_id}`
- `DELETE /api/projects/{project_id}`
- `POST /api/simulations/run`
- `GET /api/simulations`
- `GET /api/dashboard`
- `GET /api/system/status`

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure environment:
   ```bash
   cp .env.example .env
   ```
3. Run the app:
   ```bash
   PYTHONPATH=src python src/main.py
   ```
4. Open:
   - UI: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

## Test

```bash
PYTHONPATH=src pytest -q
```

## Docker

Build and run:

```bash
docker build -t quantum-wavepacket-platform .
docker run --rm -p 8000:8000 quantum-wavepacket-platform
```

## Notes

- The simulation engine is GPU-ready at the architecture level (monitoring endpoint included); numerical kernel runs on CPU in this implementation.
- SQLite is default for local persistence. Use `DATABASE_URL` to switch to production databases.
- Set a strong `JWT_SECRET_KEY` in production.
