import numpy as np
import matplotlib.pyplot as plt

from core.wavefunction import gaussian_wavepacket
from core.potentials import square_barrier
from solvers.split_operator import evolve, precompute_k

# -----------------------
# Grid
# -----------------------
N = 1024
x = np.linspace(-50, 50, N)
dx = x[1] - x[0]

# -----------------------
# Time params
# -----------------------
dt = 0.01
steps = 300

# -----------------------
# Initial state
# -----------------------
psi = gaussian_wavepacket(x, x0=-15, k0=6, sigma=1.5)

# -----------------------
# Potential
# -----------------------
V = square_barrier(x, height=1.0, width=3.0, center=0.0)

# -----------------------
# Precompute momentum grid (IMPORTANT optimization)
# -----------------------
k = precompute_k(N, dx)

# -----------------------
# Plot setup
# -----------------------
plt.ion()

# -----------------------
# Time evolution
# -----------------------
for t in range(steps):
    psi = evolve(psi, V, x, dt, k=k)

    if t % 5 == 0:
        plt.clf()
        plt.plot(x, np.abs(psi)**2)
        plt.ylim(0, 1.2)
        plt.title("Quantum Wave Packet Evolution")
        plt.pause(0.01)

plt.ioff()
plt.show()
