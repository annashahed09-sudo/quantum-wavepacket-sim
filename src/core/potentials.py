"""Quantum potential primitives for the Time-Dependent Schrödinger Equation.

Provides a library of 1D potential functions commonly used in quantum mechanics
simulations — barriers, wells, traps, and combinations.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt


def square_barrier(
    x: npt.NDArray[np.floating],
    height: float = 1.0,
    width: float = 2.0,
    center: float = 0.0,
) -> npt.NDArray[np.floating]:
    """Finite square potential barrier.

    .. code-block:: text

        V(x) = height  for |x - center| < width/2
               0       otherwise

    Parameters
    ----------
    x : ndarray
        Spatial grid points.
    height : float, optional
        Barrier height (default 1.0).
    width : float, optional
        Barrier full width (default 2.0).
    center : float, optional
        Centre position of the barrier (default 0.0).

    Returns
    -------
    ndarray
        Potential energy values evaluated on *x*.
    """
    V = np.zeros_like(x)
    V[np.abs(x - center) < width / 2] = height
    return V


def gaussian_barrier(
    x: npt.NDArray[np.floating],
    height: float = 1.0,
    sigma: float = 1.0,
    center: float = 0.0,
) -> npt.NDArray[np.floating]:
    """Gaussian (smooth) potential barrier.

    .. code-block:: text

        V(x) = height * exp(-(x - center)^2 / (2 * sigma^2))

    The smooth profile avoids the high-frequency components introduced by a
    square barrier, making it more physically realistic in many scenarios and
    numerically better-behaved under FFT-based propagation.

    Parameters
    ----------
    x : ndarray
        Spatial grid points.
    height : float, optional
        Peak barrier height (default 1.0).
    sigma : float, optional
        Width of the Gaussian (default 1.0).
    center : float, optional
        Centre position (default 0.0).

    Returns
    -------
    ndarray
        Potential energy values evaluated on *x*.
    """
    return height * np.exp(-((x - center) ** 2) / (2 * sigma**2))


def harmonic_oscillator(
    x: npt.NDArray[np.floating],
    omega: float = 1.0,
    mass: float = 1.0,
    center: float = 0.0,
) -> npt.NDArray[np.floating]:
    r"""Harmonic oscillator (quadratic trap) potential.

    .. code-block:: text

        V(x) = 0.5 * mass * omega^2 * (x - center)^2

    The harmonic oscillator is the cornerstone of quantum mechanics — its
    eigenstates are Hermite--Gauss functions and it models trapping potentials,
    molecular vibrations, and quantum optics.

    Parameters
    ----------
    x : ndarray
        Spatial grid points.
    omega : float, optional
        Angular frequency (default 1.0).
    mass : float, optional
        Particle mass (default 1.0).
    center : float, optional
        Centre of the trap (default 0.0).

    Returns
    -------
    ndarray
        Potential energy values evaluated on *x*.
    """
    return 0.5 * mass * omega**2 * (x - center) ** 2


def double_well(
    x: npt.NDArray[np.floating],
    height: float = 1.0,
    width: float = 4.0,
    barrier_width: float = 1.0,
    center: float = 0.0,
) -> npt.NDArray[np.floating]:
    """Symmetric double-well potential.

    .. code-block:: text

        V(x) = 0                              for wells
               height                          for the central barrier
               height (falloff beyond wells)   outside

    The double well is the textbook system for studying quantum tunnelling
    and energy-level splitting (symmetric / anti-symmetric superposition
    states).

    Parameters
    ----------
    x : ndarray
        Spatial grid points.
    height : float, optional
        Barrier height between wells (default 1.0).
    width : float, optional
        Full width from left well centre to right well centre (default 4.0).
    barrier_width : float, optional
        Width of the central barrier (default 1.0).
    center : float, optional
        Centre of the double-well system (default 0.0).

    Returns
    -------
    ndarray
        Potential energy values evaluated on *x*.
    """
    half_barrier = barrier_width / 2
    half_width = width / 2
    left_centre = center - half_width
    right_centre = center + half_width

    V = np.full_like(x, height)
    # Left well
    V[np.abs(x - left_centre) < half_barrier] = 0.0
    # Right well
    V[np.abs(x - right_centre) < half_barrier] = 0.0
    return V


def finite_well(
    x: npt.NDArray[np.floating],
    depth: float = 1.0,
    width: float = 2.0,
    center: float = 0.0,
) -> npt.NDArray[np.floating]:
    """Finite square potential well (the inverse of a barrier).

    .. code-block:: text

        V(x) = -depth  for |x - center| < width/2
               0       otherwise

    A finite well traps bound states with discrete energies and is the
    1D reduction of the quantum well structures used in semiconductor
    physics and quantum dots.

    Parameters
    ----------
    x : ndarray
        Spatial grid points.
    depth : float, optional
        Well depth (positive; sign flipped internally, default 1.0).
    width : float, optional
        Well full width (default 2.0).
    center : float, optional
        Centre position of the well (default 0.0).

    Returns
    -------
    ndarray
        Potential energy values evaluated on *x*.
    """
    V = np.zeros_like(x)
    V[np.abs(x - center) < width / 2] = -abs(depth)
    return V
