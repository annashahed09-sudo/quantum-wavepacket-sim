from .errors import AuthorizationError
from .models import Role


_ALLOWED_SIMULATION_ROLES = {
    Role.USER,
    Role.RESEARCHER,
    Role.ADMINISTRATOR,
    Role.ENTERPRISE,
}


def require_simulation_permission(role: Role) -> None:
    if role not in _ALLOWED_SIMULATION_ROLES:
        raise AuthorizationError("role is not permitted to run simulations")


def can_override_limits(role: Role) -> bool:
    return role in {Role.ADMINISTRATOR, Role.ENTERPRISE}
