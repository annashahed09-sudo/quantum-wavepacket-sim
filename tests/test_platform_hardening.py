import os
import sys
import unittest

sys.path.append(os.path.abspath("src"))

from platform_hardening.errors import (  # noqa: E402
    AuthorizationError,
    ConcurrencyError,
    QuotaExceededError,
    TimeoutError,
    ValidationError,
)
from platform_hardening.models import Role, SimulationRequest  # noqa: E402
from platform_hardening.policy import ServerLimits  # noqa: E402
from platform_hardening.quota import InMemoryQuotaManager  # noqa: E402
from platform_hardening.service import SimulationService  # noqa: E402


def build_request(**overrides):
    payload = dict(
        user_id="user-1",
        role=Role.USER,
        grid_points=256,
        steps=4,
        dt=0.01,
        x_min=-20.0,
        x_max=20.0,
        x0=-5.0,
        k0=5.0,
        sigma=1.2,
        barrier_height=1.0,
        barrier_width=2.0,
        barrier_center=0.0,
        requires_gpu=False,
        estimated_gpu_seconds=0.0,
        approved_by_server=False,
    )
    payload.update(overrides)
    return SimulationRequest(**payload)


class PlatformHardeningTests(unittest.TestCase):
    def test_guest_cannot_run(self):
        service = SimulationService()
        with self.assertRaises(AuthorizationError):
            service.run(build_request(role=Role.GUEST))

    def test_grid_limit_is_enforced(self):
        limits = ServerLimits(max_fft_grid_size=128)
        service = SimulationService(limits=limits)
        with self.assertRaises(ValidationError):
            service.run(build_request(grid_points=256))

    def test_expensive_request_needs_explicit_approval(self):
        limits = ServerLimits(expensive_steps_threshold=2)
        service = SimulationService(limits=limits)
        with self.assertRaises(ValidationError):
            service.run(build_request(steps=3, approved_by_server=False))

    def test_admin_can_override_explicit_approval(self):
        limits = ServerLimits(expensive_steps_threshold=2)
        service = SimulationService(limits=limits)
        result = service.run(build_request(role=Role.ADMINISTRATOR, steps=3, approved_by_server=False))
        self.assertEqual(result.steps_executed, 3)

    def test_quota_enforced(self):
        limits = ServerLimits(daily_request_limit=1, monthly_request_limit=1)
        service = SimulationService(limits=limits, quota_manager=InMemoryQuotaManager())
        service.run(build_request(approved_by_server=True))
        with self.assertRaises(QuotaExceededError):
            service.run(build_request(approved_by_server=True))

    def test_timeout_enforced(self):
        limits = ServerLimits(max_simulation_duration_seconds=0.0)
        service = SimulationService(limits=limits)
        with self.assertRaises(TimeoutError):
            service.run(build_request(approved_by_server=True, steps=1))

    def test_concurrency_limit_enforced(self):
        limits = ServerLimits(max_concurrent_jobs=0)
        service = SimulationService(limits=limits)
        with self.assertRaises(ConcurrencyError):
            service.run(build_request(approved_by_server=True))

    def test_happy_path_returns_norm(self):
        service = SimulationService()
        result = service.run(build_request(approved_by_server=True))
        self.assertEqual(result.steps_executed, 4)
        self.assertGreater(result.final_norm, 0.0)


if __name__ == "__main__":
    unittest.main()
