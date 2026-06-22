import numpy as np

def gaussian_wavepacket(x, x0=-10, k0=5, sigma=1.0):
    """
    Normalized Gaussian wave packet with momentum kick.
    """
    norm = (1 / (sigma * np.sqrt(np.pi))) ** 0.5
    psi = norm * np.exp(-(x - x0)**2 / (2 * sigma**2)) * np.exp(1j * k0 * x)
    return psi
    
