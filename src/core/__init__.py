"""Core quantum physics primitives — wavefunctions and potentials for TDSE simulation."""

from core.potentials import (
    double_well,
    finite_well,
    gaussian_barrier,
    harmonic_oscillator,
    square_barrier,
)
from core.wavefunction import gaussian_wavepacket

__all__ = [
    "gaussian_wavepacket",
    "square_barrier",
    "harmonic_oscillator",
    "gaussian_barrier",
    "double_well",
    "finite_well",
]
