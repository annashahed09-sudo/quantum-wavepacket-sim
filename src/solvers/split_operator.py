"""Split-operator Fourier method for TDSE time propagation.

Implements the second-order split-operator (Trotter--Suzuki) scheme:

    1. Half potential step in position space
    2. Full kinetic step in momentum (FFT) space
    3. Half potential step in position space

This is a unitary, symplectic integrator that preserves norm to machine
precision (up to FFT rounding) for any time step.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt


def precompute_k(
    N: int,
    dx: float,
    hbar: float = 1.0,
) -> npt.NDArray[np.floating]:
    """Precompute angular wave-number grid for the kinetic operator.

    Uses :func:`numpy.fft.fftfreq` to generate the Fourier-domain angular
    wave-numbers :math:`k` such that :math:`-\\pi/\\Delta x \\le k < \\pi/\\Delta x`.

    Parameters
    ----------
    N : int
        Number of spatial grid points.
    dx : float
        Grid spacing.
    hbar : float, optional
        Reduced Planck constant (default 1.0 — atomic units).

    Returns
    -------
    ndarray
        Angular wave-number array of length *N* (hbar is **not** folded in).
    """
    k: npt.NDArray[np.floating] = np.fft.fftfreq(N, d=dx) * 2.0 * np.pi
    return k


def evolve(
    psi: npt.NDArray[np.complexfloating],
    V: npt.NDArray[np.floating],
    x: npt.NDArray[np.floating],
    dt: float,
    k: npt.NDArray[np.floating] | None = None,
    m: float = 1.0,
    hbar: float = 1.0,
) -> npt.NDArray[np.complexfloating]:
    """Single time step via the second-order split-operator method.

    Parameters
    ----------
    psi : ndarray (complex)
        Current wavefunction values on *x*.
    V : ndarray (float)
        Potential energy evaluated on *x*.
    x : ndarray (float)
        Spatial grid.
    dt : float
        Time step (atomic units when *hbar = m = 1*).
    k : ndarray (float) or None, optional
        Pre-computed wave-number grid.  Computed from *x* if None (default).
    m : float, optional
        Particle mass (default 1.0).
    hbar : float, optional
        Reduced Planck constant (default 1.0 — atomic units).

    Returns
    -------
    ndarray (complex)
        Wavefunction after one time step.
    """
    N = len(x)
    dx = x[1] - x[0]

    # Pre-compute wave-numbers on first call or if not provided.
    if k is None:
        k_local = precompute_k(N, dx, hbar)
    else:
        k_local = k

    # --- half potential step (position space) ---
    psi = psi * np.exp(-1j * V * dt / (2.0 * hbar))

    # --- full kinetic step (momentum / FFT space) ---
    psi_k = np.fft.fft(psi)
    kinetic_phase = np.exp(-1j * (hbar * k_local**2) * dt / (2.0 * m))
    psi_k *= kinetic_phase
    psi = np.fft.ifft(psi_k)

    # --- half potential step (position space) ---
    psi = psi * np.exp(-1j * V * dt / (2.0 * hbar))

    return psi
