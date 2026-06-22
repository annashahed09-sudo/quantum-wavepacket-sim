# Quantum Wave Packet Simulator (TDSE Engine)

GPU-ready numerical solver for the Time-Dependent Schrödinger Equation using spectral methods to simulate quantum wave packet dynamics, tunneling, and scattering in one spatial dimension.

---

## Overview

This project is a computational physics framework for solving the Time-Dependent Schrödinger Equation (TDSE). It simulates the evolution of quantum wave packets under external potentials, enabling visualization and analysis of tunneling, scattering, interference, and dispersion phenomena.

The design is structured to evolve from a CPU-based numerical prototype into a GPU-accelerated and eventually multi-GPU distributed simulation system.

---

## Key Computational Insight

The dominant computational cost arises from FFT-based kinetic propagation in spectral space. This makes the solver memory-bandwidth bound and highly suitable for GPU acceleration using parallel FFT implementations.

---

## Governing Equation

The system solves the Time-Dependent Schrödinger Equation:

iħ ∂ψ(x,t)/∂t = [−(ħ² / 2m) ∇² + V(x)] ψ(x,t)

Where:
- ψ(x,t): complex wavefunction
- V(x): potential energy function
- ħ: reduced Planck constant

Observable quantity:
- |ψ(x,t)|² → probability density

---

## Numerical Method

### Split-Operator Fourier Method

The time evolution operator is approximated as:

U(Δt) ≈ e^(−iVΔt/2ħ) · e^(−iTΔt/ħ) · e^(−iVΔt/2ħ)

Where:
- T is the kinetic energy operator
- FFT is used to evaluate kinetic propagation in momentum space

Properties:
- Second-order accuracy in time
- Approximately unitary (norm-preserving up to numerical precision)
- Highly parallelizable and GPU-friendly

---

## Physical Phenomena Simulated

- Quantum tunneling through potential barriers
- Wave packet scattering and reflection
- Free particle dispersion
- Quantum interference effects
- Probability conservation dynamics

---

## Project Architecture

```text
src/
├── core/
│   ├── wavefunction.py
│   ├── potentials.py
│
├── solvers/
│   ├── split_operator.py
│
├── main.py

Instal dependencies 
pip install numpy scipy matplotlib

Run simulations
python src/main.py

License
MIT License
