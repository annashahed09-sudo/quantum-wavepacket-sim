import numpy as np
import matplotlib.pyplot as plt

from core.wavefunction import gaussian_wavepacket
from core.potentials import square_barrier
from solvers.split_operator import evolve

# -----------------------
# Simulation parameters
# -----------------------
N = 1024
x = np.linspace(-50, 50, N)
dx = x[1] - x[0]

dt = 0.01
steps = 300

# -----------------------
# Initial wavefunction
# -----------------------
psi = gaussian_wavepacket(x, x0=-15, k0=6, sigma=1.5)

# -----------------------
# Potential
# -----------------------
V = square_barrier(x, height=1.0, width=3.0, center=0.0)

# -----------------------
# Visualization setup
# -----------------------
plt.ion()

# -----------------------
# Time evolution loop
# -----------------------
for t in range(steps):
    psi = evolve(psi, V, x, dt)

    if t % 5 == 0:
        plt.clf()
        plt.plot(x, np.abs(psi)**2)
        plt.ylim(0, 1.2)
        plt.title("Quantum Wave Packet Evolution")
        plt.pause(0.01)

plt.ioff()
plt.show()
