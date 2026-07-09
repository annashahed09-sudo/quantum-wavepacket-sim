export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function createSimulation(config: unknown): Promise<{ run_id: string }> {
  const response = await fetch(`${API_BASE}/simulation/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ config })
  });
  if (!response.ok) {
    throw new Error("Failed to create simulation");
  }
  return response.json();
}

export async function runSimulation(runId: string, config: unknown): Promise<void> {
  const response = await fetch(`${API_BASE}/simulation/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ run_id: runId, config })
  });
  if (!response.ok) {
    throw new Error("Failed to start simulation");
  }
}
