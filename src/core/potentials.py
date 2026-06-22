import numpy as np

def square_barrier(x, height=1.0, width=2.0, center=0.0):
    """
    Finite square potential barrier.
    """
    V = np.zeros_like(x)
    V[np.abs(x - center) < width / 2] = height
    return V
