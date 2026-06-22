import numpy as np

def precompute_k(N, dx, hbar=1.0):
    k = np.fft.fftfreq(N, d=dx) * 2 * np.pi
    return k


def evolve(psi, V, x, dt, k=None, m=1.0, hbar=1.0):
    """
    Split-Operator Fourier evolution step
    """

    N = len(x)
    dx = x[1] - x[0]

    # precompute k if not passed
    if k is None:
        k = precompute_k(N, dx, hbar)

    # --- half potential step ---
    psi = psi * np.exp(-1j * V * dt / (2 * hbar))

    # --- kinetic step (FFT domain) ---
    psi_k = np.fft.fft(psi)
    kinetic_phase = np.exp(-1j * (hbar * k**2) * dt / (2 * m))
    psi_k *= kinetic_phase
    psi = np.fft.ifft(psi_k)

    # --- half potential step ---
    psi = psi * np.exp(-1j * V * dt / (2 * hbar))

    return psi
