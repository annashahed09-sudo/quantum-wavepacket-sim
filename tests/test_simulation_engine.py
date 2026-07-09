import numpy as np

from core.potentials import square_barrier
from core.wavefunction import gaussian_wavepacket
from solvers.split_operator import evolve, precompute_k


def test_split_operator_approximately_preserves_norm():
    n = 512
    x = np.linspace(-40, 40, n)
    dx = x[1] - x[0]

    psi = gaussian_wavepacket(x, x0=-8, k0=4, sigma=1.2)
    v = square_barrier(x, height=1.0, width=2.0, center=0.0)
    k = precompute_k(n, dx)

    norm_initial = float(np.sum(np.abs(psi) ** 2) * dx)

    for _ in range(120):
        psi = evolve(psi, v, x, dt=0.01, k=k)

    norm_final = float(np.sum(np.abs(psi) ** 2) * dx)

    assert abs(norm_final - norm_initial) < 1e-3
