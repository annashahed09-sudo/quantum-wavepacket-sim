import numpy as np
import matplotlib.pyplot as plt

from core.wavefunction import gaussian_wavepacket
from core.potentials import square_barrier
from solvers.split_operator import evolve, precompute_k

# -----------------------
# Spatial grid
# -----------------------
N = 1024
x = np.linspace(-50, 50, N)
dx = x[1] - x[0]

# -----------------------
# Time parameters
# -----------------------
dt = 0.01
steps = 300

# -----------------------
# Initial wavefunction
# -----------------------
psi = gaussian_wavepacket(x, x0=-15, k0=6, sigma=1.5)

# -----------------------
# Potential barrier
# -----------------------
V = square_barrier(x, height=1.0, width=3.0, center=0.0)

# -----------------------
# Momentum grid (FFT space)
# -----------------------
k = precompute_k(N, dx)

# -----------------------
# Plot setup
# -----------------------
plt.ion()
fig, ax = plt.subplots()

line, = ax.plot(x, np.abs(psi)**2)

ax.set_ylim(0, 1.2)
ax.set_title("Quantum Wave Packet Evolution")
ax.set_xlabel("x")
ax.set_ylabel("|ψ(x,t)|²")

# -----------------------
# Time evolution loop
# -----------------------
for t in range(steps):
    psi = evolve(psi, V, x, dt, k)

    if t % 5 == 0:
        line.set_ydata(np.abs(psi)**2)
        plt.pause(0.01)

plt.ioff()
plt.show()
