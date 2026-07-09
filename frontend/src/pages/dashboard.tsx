import { useMemo, useState } from "react";

import { SimulationChart } from "../components/SimulationChart";
import { createSimulation, runSimulation } from "../services/api";

const defaultConfig = {
  name: "dashboard-run",
  backend: "auto",
  precision: "complex128",
  grid: { dimension: 1, points: 512, x_min: -40, x_max: 40, boundary: "periodic" },
  time: { dt: 0.01, total_time: 2.0, save_stride: 5, adaptive_timestep: false },
  particle: { mass: 1.0, hbar: 1.0 },
  initial_state: { x0: -12, k0: 5.5, sigma: 1.3 },
  potential: { kind: "square_barrier", height: 1.0, width: 3.0, center: 0.0, omega: 0.5 }
};

export default function DashboardPage() {
  const [status, setStatus] = useState("idle");
  const [frame, setFrame] = useState<any>(null);

  const x = useMemo(() => {
    const g = defaultConfig.grid;
    const step = (g.x_max - g.x_min) / (g.points - 1);
    return Array.from({ length: g.points }, (_, i) => g.x_min + i * step);
  }, []);

  const start = async () => {
    setStatus("creating");
    const created = await createSimulation(defaultConfig);
    await runSimulation(created.run_id, defaultConfig);

    setStatus("streaming");
    const socket = new WebSocket("ws://localhost:8000/live");
    socket.onopen = () => socket.send(JSON.stringify({ config: defaultConfig }));
    socket.onmessage = (event) => setFrame(JSON.parse(event.data));
    socket.onclose = () => setStatus("complete");
  };

  return (
    <main style={{ padding: 24, backgroundColor: "#080d1f", color: "#ecf1ff", minHeight: "100vh" }}>
      <h1>Simulation Builder</h1>
      <button onClick={start} style={{ padding: "10px 14px", borderRadius: 8 }}>
        Run Simulation
      </button>
      <p>Status: {status}</p>
      {frame && (
        <>
          <p>
            t={frame.time.toFixed(3)} | norm={frame.diagnostics.norm.toFixed(6)} | Δnorm=
            {frame.diagnostics.norm_error.toExponential(2)}
          </p>
          <SimulationChart
            x={x}
            probability={frame.probability_density}
            realPart={frame.real_component}
            imaginaryPart={frame.imaginary_component}
          />
        </>
      )}
    </main>
  );
}
