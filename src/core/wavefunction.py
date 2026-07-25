"""Initial wavefunction generators for TDSE simulations.

Provides factory functions that create normalised quantum states on a 1D
spatial grid, ready for time propagation.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt


def gaussian_wavepacket(
    x: npt.NDArray[np.floating],
    x0: float = -10.0,
    k0: float = 5.0,
    sigma: float = 1.0,
) -> npt.NDArray[np.complexfloating]:
    """Normalised Gaussian wavepacket with a momentum kick.

    .. code-block:: text

        psi(x) = N * exp(-(x - x0)^2 / (2 * sigma^2)) * exp(i * k0 * x)

    The wavepacket is localised around *x0* with width *sigma* and an initial
    momentum *hbar * k0*.  It is the standard initial state for scattering
    and tunneling simulations.

    Parameters
    ----------
    x : ndarray
        Spatial grid points.
    x0 : float, optional
        Centre of the wavepacket (default -10.0).
    k0 : float, optional
        Initial wave-number (momentum = hbar * k0, default 5.0).
    sigma : float, optional
        Width of the wavepacket (default 1.0).

    Returns
    -------
    ndarray (complex)
        Normalised wavefunction values on *x*.
    """
    norm = (1.0 / (sigma * np.sqrt(np.pi))) ** 0.5
    psi: npt.NDArray[np.complexfloating] = (
        norm * np.exp(-((x - x0) ** 2) / (2 * sigma**2)) * np.exp(1j * k0 * x)
    )
    return psi


def plane_wave(
    x: npt.NDArray[np.floating],
    k0: float = 5.0,
) -> npt.NDArray[np.complexfloating]:
    """Plane wave (constant amplitude, definite momentum).

    .. code-block:: text

        psi(x) = exp(i * k0 * x) / sqrt(L)

    where *L* is the grid extent.  The state is momentum eigenstate
    *exp(i k0 x)* normalised on the simulation domain.

    Parameters
    ----------
    x : ndarray
        Spatial grid points.
    k0 : float, optional
        Wave-number (default 5.0).

    Returns
    -------
    ndarray (complex)
        Normalised plane wave on *x*.
    """
    L = x[-1] - x[0]
    psi: npt.NDArray[np.complexfloating] = np.exp(1j * k0 * x) / np.sqrt(L)
    return psi


def eigenstate_n(n: int, x: npt.NDArray[np.floating], x0: float = 0.0, sigma: float = 1.0) -> npt.NDArray[np.complexfloating]:
    """Approximate *n*-th harmonic-oscillator eigenstate (Hermite--Gauss).

    Uses the analytic Hermite--Gauss functions to generate excited states of
    the harmonic oscillator.  Intended for testing the solver against known
    stationary states.

    Parameters
    ----------
    n : int
        Quantum number (0 = ground state).
    x : ndarray
        Spatial grid points.
    x0 : float, optional
        Centre position (default 0.0).
    sigma : float, optional
        Width parameter (default 1.0) — sets oscillator length scale.

    Returns
    -------
    ndarray (complex)
        Normalised *n*-th eigenstate.
    """
    from numpy.polynomial.hermite import hermval

    xi = (x - x0) / sigma
    coeffs = np.zeros(n + 1)
    coeffs[n] = 1.0
    H_n = hermval(xi, coeffs)
    norm = (1.0 / (sigma * np.sqrt(np.pi) * 2**n * _factorial(n))) ** 0.5  # type: ignore[arg-type]
    psi: npt.NDArray[np.complexfloating] = norm * H_n * np.exp(-(xi**2) / 2)
    return psi


def _factorial(n: int) -> int:
    """Small-integer factorial (avoids scipy.special import)."""
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
