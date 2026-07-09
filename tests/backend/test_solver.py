from backend.core.config import SimulationConfig
from backend.solvers.split_operator import SplitOperatorSolver


def test_solver_preserves_norm_with_small_error():
    cfg = SimulationConfig(
        grid={"points": 256, "x_min": -20, "x_max": 20},
        time={"dt": 0.005, "total_time": 0.3, "save_stride": 2},
    )
    frames, summary = SplitOperatorSolver(cfg).run()

    assert frames
    assert summary.frames_saved == len(frames)
    assert frames[-1].diagnostics["norm_error"] < 5e-3
