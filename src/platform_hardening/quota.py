from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import QuotaExceededError
from .policy import ServerLimits


@dataclass
class UserQuotaState:
    daily_date: str
    daily_requests: int
    daily_gpu_seconds: float
    monthly_key: str
    monthly_requests: int
    monthly_gpu_seconds: float


class InMemoryQuotaManager:
    """Simple per-user quota manager for production policy enforcement points."""

    def __init__(self) -> None:
        self._state: dict[str, UserQuotaState] = {}

    def _current_keys(self) -> tuple[str, str]:
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m")

    def _get_state(self, user_id: str) -> UserQuotaState:
        daily_date, monthly_key = self._current_keys()
        state = self._state.get(user_id)
        if state is None:
            state = UserQuotaState(
                daily_date=daily_date,
                daily_requests=0,
                daily_gpu_seconds=0.0,
                monthly_key=monthly_key,
                monthly_requests=0,
                monthly_gpu_seconds=0.0,
            )
            self._state[user_id] = state
            return state

        if state.daily_date != daily_date:
            state.daily_date = daily_date
            state.daily_requests = 0
            state.daily_gpu_seconds = 0.0

        if state.monthly_key != monthly_key:
            state.monthly_key = monthly_key
            state.monthly_requests = 0
            state.monthly_gpu_seconds = 0.0

        return state

    def consume(self, user_id: str, limits: ServerLimits, estimated_gpu_seconds: float = 0.0) -> None:
        state = self._get_state(user_id)

        if state.daily_requests + 1 > limits.daily_request_limit:
            raise QuotaExceededError("daily request limit exceeded")

        if state.monthly_requests + 1 > limits.monthly_request_limit:
            raise QuotaExceededError("monthly request limit exceeded")

        if state.daily_gpu_seconds + estimated_gpu_seconds > limits.daily_gpu_seconds_limit:
            raise QuotaExceededError("daily gpu seconds limit exceeded")

        if state.monthly_gpu_seconds + estimated_gpu_seconds > limits.monthly_gpu_seconds_limit:
            raise QuotaExceededError("monthly gpu seconds limit exceeded")

        state.daily_requests += 1
        state.monthly_requests += 1
        state.daily_gpu_seconds += estimated_gpu_seconds
        state.monthly_gpu_seconds += estimated_gpu_seconds
