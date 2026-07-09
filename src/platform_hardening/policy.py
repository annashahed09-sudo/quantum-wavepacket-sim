from dataclasses import dataclass


@dataclass(frozen=True)
class ServerLimits:
    max_fft_grid_size: int = 4096
    max_simulation_steps: int = 10_000
    max_simulation_duration_seconds: float = 20.0
    max_memory_bytes_per_job: int = 512 * 1024 * 1024
    max_concurrent_jobs: int = 4
    daily_request_limit: int = 250
    monthly_request_limit: int = 5_000
    daily_gpu_seconds_limit: float = 1_200.0
    monthly_gpu_seconds_limit: float = 20_000.0
    expensive_steps_threshold: int = 2_000
    expensive_grid_threshold: int = 2_048
