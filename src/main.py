from platform_hardening import Role, ServerLimits, SimulationRequest, SimulationService


def main() -> None:
    service = SimulationService(limits=ServerLimits())
    request = SimulationRequest(
        user_id="local-demo-user",
        role=Role.RESEARCHER,
        grid_points=1024,
        steps=300,
        dt=0.01,
        x_min=-50.0,
        x_max=50.0,
        x0=-15.0,
        k0=6.0,
        sigma=1.5,
        barrier_height=1.0,
        barrier_width=3.0,
        barrier_center=0.0,
        approved_by_server=True,
    )
    result = service.run(request)
    print(
        "Simulation complete:",
        f"grid={result.grid_points}",
        f"steps={result.steps_executed}",
        f"norm={result.final_norm:.6f}",
        f"elapsed={result.elapsed_seconds:.3f}s",
    )


if __name__ == "__main__":
    main()
