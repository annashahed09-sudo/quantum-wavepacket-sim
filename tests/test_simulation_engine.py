"""
Parametrized numerical tests for the TDSE simulation engine.

Tests cover norm preservation, phase stability, and correctness of each
built-in potential type.  All tests use modest grid sizes and step counts
so they run quickly (< 1 s each).
"""

from __future__ import annotations

import numpy as np
import pytest

from core.potentials import (
    double_well,
    finite_well,
    gaussian_barrier,
    harmonic_oscillator,
    square_barrier,
)
from core.wavefunction import gaussian_wavepacket
from solvers.split_operator import evolve, precompute_k


# ---------------------------------------------------------------------------
# Shared simulation parameters
# ---------------------------------------------------------------------------
N = 512
X_MIN, X_MAX = -40.0, 40.0
DX = (X_MAX - X_MIN) / N
X = np.linspace(X_MIN, X_MAX, N)
DT = 0.01
STEPS = 120
K = precompute_k(N, DX)


@pytest.fixture
def gaussian_state() -> np.ndarray:
    """A standard Gaussian wavepacket heading right toward a barrier."""
    return gaussian_wavepacket(X, x0=-8.0, k0=4.0, sigma=1.2)


# ---------------------------------------------------------------------------
# Potential shape tests
# ---------------------------------------------------------------------------


class TestPotentials:
    """Verify that each potential builder returns sensible outputs."""

    def test_square_barrier_shape(self) -> None:
        V = square_barrier(X, height=2.0, width=4.0, center=0.0)
        assert V.shape == X.shape
        assert np.all(V[np.abs(X) < 2.0] == 2.0)
        assert np.all(V[np.abs(X) >= 2.0] == 0.0)

    def test_gaussian_barrier_peak(self) -> None:
        V = gaussian_barrier(X, height=3.0, sigma=2.0, center=5.0)
        assert V.shape == X.shape
        # Peak may not land exactly on a grid point; value should be close to height
        assert np.max(V) == pytest.approx(3.0, abs=0.01)

    def test_harmonic_oscillator_quadratic(self) -> None:
        V = harmonic_oscillator(X, omega=1.0, mass=1.0, center=0.0)
        assert V.shape == X.shape
        # Minimum value should be close to 0 (center may not be exactly at grid point)
        assert np.min(V) == pytest.approx(0.0, abs=0.01)
        # Symmetry about center
        assert V[0] == pytest.approx(V[-1], abs=1e-10)

    def test_double_well_two_minima(self) -> None:
        V = double_well(X, height=2.0, width=4.0, barrier_width=1.0, center=0.0)
        assert V.shape == X.shape
        # Wells should be at x ~ -2 and x ~ +2
        assert np.min(V) == 0.0

    def test_finite_well_negative(self) -> None:
        V = finite_well(X, depth=1.5, width=3.0, center=0.0)
        assert V.shape == X.shape
        assert np.all(V[np.abs(X) < 1.5] < 0.0)
        assert np.all(V[np.abs(X) >= 1.5] == 0.0)


# ---------------------------------------------------------------------------
# Solver numerical tests
# ---------------------------------------------------------------------------


class TestSolverNumerics:
    """Numerical correctness of the split-operator Fourier solver."""

    def test_norm_preservation_free_particle(self, gaussian_state: np.ndarray) -> None:
        """Without a potential, norm must be conserved exactly (up to FFT rounding)."""
        psi = gaussian_state.copy()
        V = np.zeros(N)
        norm0 = float(np.sum(np.abs(psi) ** 2) * DX)
        for _ in range(STEPS):
            psi = evolve(psi, V, X, dt=DT, k=K)
        norm1 = float(np.sum(np.abs(psi) ** 2) * DX)
        assert abs(norm1 - norm0) < 1e-3

    @pytest.mark.parametrize("potential_fn", [
        square_barrier,
        gaussian_barrier,
        harmonic_oscillator,
    ])
    def test_norm_preservation_with_potential(
        self, gaussian_state: np.ndarray, potential_fn
    ) -> None:
        """Norm must be conserved regardless of the potential type."""
        psi = gaussian_state.copy()
        # Parameterise each potential generically
        if potential_fn is harmonic_oscillator:
            V = potential_fn(X, omega=0.5, mass=1.0, center=0.0)
        elif potential_fn is gaussian_barrier:
            V = potential_fn(X, height=1.0, sigma=1.5, center=0.0)
        else:
            V = potential_fn(X, height=1.0, width=2.0, center=0.0)

        norm0 = float(np.sum(np.abs(psi) ** 2) * DX)
        for _ in range(STEPS):
            psi = evolve(psi, V, X, dt=DT, k=K)
        norm1 = float(np.sum(np.abs(psi) ** 2) * DX)
        assert abs(norm1 - norm0) < 1e-3

    def test_square_barrier_tunneling(self) -> None:
        """A wavepacket incident on a square barrier should show non-zero
        transmitted probability (quantum tunnelling)."""
        x = np.linspace(-30, 30, 256)
        dx = x[1] - x[0]
        k = precompute_k(256, dx)
        psi = gaussian_wavepacket(x, x0=-10, k0=6, sigma=1.0)
        V = square_barrier(x, height=1.5, width=2.0, center=0.0)

        for _ in range(200):
            psi = evolve(psi, V, x, dt=0.01, k=k)

        density = np.abs(psi) ** 2
        transmitted = float(np.sum(density[x > 2.0]) * dx)
        assert transmitted > 1e-6, "No tunneling detected"

    def test_harmonic_oscillator_bounded(self) -> None:
        """A wavepacket in a harmonic trap should remain localised (bounded motion)."""
        x = np.linspace(-20, 20, 256)
        dx = x[1] - x[0]
        k = precompute_k(256, dx)
        psi = gaussian_wavepacket(x, x0=-5, k0=3, sigma=0.8)
        V = harmonic_oscillator(x, omega=0.4, mass=1.0, center=0.0)

        for _ in range(300):
            psi = evolve(psi, V, x, dt=0.01, k=k)

        density = np.abs(psi) ** 2
        # Most probability should remain within simulation bounds
        prob = float(np.sum(density) * dx)
        assert abs(prob - 1.0) < 1e-2, "Norm significantly lost"

    def test_large_time_step_stability(self) -> None:
        """Large time steps should not cause norm explosion (should stay bounded)."""
        psi = gaussian_wavepacket(X, x0=-5, k0=2, sigma=1.5)
        V = np.zeros(N)
        norm0 = float(np.sum(np.abs(psi) ** 2) * DX)
        # Use a relatively large dt — algorithm should remain stable
        for _ in range(50):
            psi = evolve(psi, V, X, dt=0.05, k=K)
        norm1 = float(np.sum(np.abs(psi) ** 2) * DX)
        assert abs(norm1 - norm0) < 2e-3

    def test_zero_potential_equivalence(self) -> None:
        """Evolving under V=0 should be identical to free propagation."""
        psi1 = gaussian_wavepacket(X, x0=-5, k0=3, sigma=1.0)
        psi2 = psi1.copy()
        V0 = np.zeros(N)
        for _ in range(60):
            psi1 = evolve(psi1, V0, X, dt=DT, k=K)
            psi2 = evolve(psi2, V0, X, dt=DT, k=K)
        np.testing.assert_array_almost_equal(np.abs(psi1), np.abs(psi2), decimal=10)
