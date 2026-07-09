from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from backend.core.config import BackendKind


class FFTBackend(Protocol):
    name: str

    def fft(self, values): ...

    def ifft(self, values): ...

    def to_device(self, values): ...

    def to_host(self, values): ...

    def exp(self, values): ...


@dataclass
class NumpyFFTBackend:
    name: str = "numpy"

    def fft(self, values):
        return np.fft.fft(values)

    def ifft(self, values):
        return np.fft.ifft(values)

    def to_device(self, values):
        return np.asarray(values)

    def to_host(self, values):
        return np.asarray(values)

    def exp(self, values):
        return np.exp(values)


@dataclass
class PyFFTWBackend:
    name: str = "pyfftw"

    def __post_init__(self):
        import pyfftw.interfaces.numpy_fft as fftw_np  # type: ignore

        self._fftw_np = fftw_np

    def fft(self, values):
        return self._fftw_np.fft(values)

    def ifft(self, values):
        return self._fftw_np.ifft(values)

    def to_device(self, values):
        return np.asarray(values)

    def to_host(self, values):
        return np.asarray(values)

    def exp(self, values):
        return np.exp(values)


@dataclass
class CuPyFFTBackend:
    name: str = "cupy"

    def __post_init__(self):
        import cupy as cp  # type: ignore

        self.cp = cp

    def fft(self, values):
        return self.cp.fft.fft(values)

    def ifft(self, values):
        return self.cp.fft.ifft(values)

    def to_device(self, values):
        return self.cp.asarray(values)

    def to_host(self, values):
        return self.cp.asnumpy(values)

    def exp(self, values):
        return self.cp.exp(values)


def _is_available(kind: BackendKind) -> bool:
    if kind == BackendKind.CUPY:
        try:
            import cupy  # noqa: F401

            return True
        except Exception:
            return False
    if kind == BackendKind.PYFFTW:
        try:
            import pyfftw  # noqa: F401

            return True
        except Exception:
            return False
    return True


def create_fft_backend(kind: BackendKind) -> FFTBackend:
    if kind == BackendKind.CUPY and _is_available(BackendKind.CUPY):
        return CuPyFFTBackend()
    if kind == BackendKind.PYFFTW and _is_available(BackendKind.PYFFTW):
        return PyFFTWBackend()
    if kind == BackendKind.NUMPY:
        return NumpyFFTBackend()

    if kind == BackendKind.AUTO:
        if _is_available(BackendKind.CUPY):
            return CuPyFFTBackend()
        if _is_available(BackendKind.PYFFTW):
            return PyFFTWBackend()
        return NumpyFFTBackend()

    return NumpyFFTBackend()
