class HardeningError(Exception):
    """Base controlled error for user-facing API responses."""


class ValidationError(HardeningError):
    """Input/request validation failure."""


class AuthorizationError(HardeningError):
    """Role is not allowed to perform this action."""


class QuotaExceededError(HardeningError):
    """Quota policy denied the operation."""


class ConcurrencyError(HardeningError):
    """Concurrent job limit exceeded."""


class TimeoutError(HardeningError):
    """Simulation execution exceeded allowed time."""
