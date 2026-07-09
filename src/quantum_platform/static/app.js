const state = {
  token: localStorage.getItem("token") || null,
  currentFrames: [],
  currentX: [],
};

const qs = (id) => document.getElementById(id);

const authPanel = qs("authPanel");
const appPanel = qs("appPanel");

function setAuthUI() {
  if (state.token) {
    authPanel.classList.add("hidden");
    appPanel.classList.remove("hidden");
    loadInitialData();
  } else {
    authPanel.classList.remove("hidden");
    appPanel.classList.add("hidden");
  }
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = "Bearer " + state.token;
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(body.detail || "Request failed");
  }
  return response.json();
}

qs("registerForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  try {
    await api("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(form.entries())),
    });
    qs("authMessage").textContent = "Registered. Please log in.";
  } catch (error) {
    qs("authMessage").textContent = error.message;
  }
});

qs("loginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  try {
    const data = await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(form.entries())),
    });
    state.token = data.access_token;
    localStorage.setItem("token", state.token);
    setAuthUI();
  } catch (error) {
    qs("authMessage").textContent = error.message;
  }
});

qs("simulationForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = Object.fromEntries(form.entries());
  ["x_min", "x_max", "dt", "x0", "k0", "sigma", "barrier_height", "barrier_width", "barrier_center"].forEach((key) => {
    payload[key] = Number(payload[key]);
  });
  ["grid_size", "steps", "sample_stride"].forEach((key) => {
    payload[key] = Number(payload[key]);
  });

  qs("autosaveStatus").textContent = "Running simulation...";
  try {
    const data = await api("/api/simulations/run", { method: "POST", body: JSON.stringify(payload) });
    state.currentFrames = data.result.frames;
    state.currentX = data.result.x;
    renderFrame(0);
    updateMetrics(data.result.stats);
    await loadDashboard();
    qs("autosaveStatus").textContent = `Simulation ${data.run_id} complete`;
  } catch (error) {
    qs("autosaveStatus").textContent = error.message;
  }
});

qs("projectForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  try {
    await api("/api/projects", { method: "POST", body: JSON.stringify(Object.fromEntries(form.entries())) });
    event.currentTarget.reset();
    await loadProjects();
  } catch (error) {
    qs("autosaveStatus").textContent = error.message;
  }
});

qs("frameSlider").addEventListener("input", (event) => {
  renderFrame(Number(event.target.value));
});

function renderFrame(index) {
  const frame = state.currentFrames[index];
  if (!frame) return;
  qs("frameLabel").textContent = `Frame ${index} (t-step ${frame.step})`;

  const canvas = qs("simulationCanvas");
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "rgba(8,14,25,0.95)";
  ctx.fillRect(0, 0, width, height);

  const maxY = Math.max(...frame.density, 1e-9);
  ctx.strokeStyle = "#36a4ff";
  ctx.lineWidth = 3;
  ctx.beginPath();

  frame.density.forEach((y, i) => {
    const xPx = (i / (frame.density.length - 1)) * width;
    const yPx = height - (y / maxY) * (height - 20);
    if (i === 0) ctx.moveTo(xPx, yPx);
    else ctx.lineTo(xPx, yPx);
  });
  ctx.stroke();

  ctx.strokeStyle = "rgba(255,255,255,0.18)";
  for (let i = 0; i <= 6; i += 1) {
    const y = (height / 6) * i;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }
}

function updateMetrics(stats) {
  const list = qs("metricsList");
  list.innerHTML = "";
  Object.entries(stats).forEach(([key, value]) => {
    const item = document.createElement("li");
    item.textContent = `${key}: ${Number(value).toFixed ? Number(value).toFixed(6) : value}`;
    list.appendChild(item);
  });
}

async function loadProjects() {
  const projects = await api("/api/projects");
  qs("projectList").innerHTML = projects
    .map((project) => `<li><strong>${project.name}</strong> — ${project.description || "No description"}</li>`)
    .join("");
}

async function loadDashboard() {
  const dashboard = await api("/api/dashboard");
  qs("recentRuns").innerHTML = dashboard.latest_runs
    .map((run) => `<li>${run.name}: norm=${run.norm_final.toFixed(6)}, E=${run.energy_final.toFixed(6)}</li>`)
    .join("");
}

async function loadSystemStatus() {
  const status = await api("/api/system/status");
  qs("systemStatus").textContent = `CPU ${status.cpu_percent}% | RAM ${status.memory_percent}% | GPU ${status.gpu_name}`;
}

async function loadInitialData() {
  await Promise.all([loadProjects(), loadDashboard(), loadSystemStatus()]);
}

qs("themeToggle").addEventListener("click", () => {
  const root = document.documentElement;
  root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
});

document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    qs("commandPalette").classList.toggle("hidden");
    qs("commandInput").focus();
  }
});

document.querySelectorAll("#commandPalette li").forEach((item) => {
  item.addEventListener("click", () => {
    if (item.dataset.command === "theme") qs("themeToggle").click();
    qs("commandPalette").classList.add("hidden");
  });
});

setInterval(() => {
  if (state.token) {
    loadSystemStatus().catch(() => {});
  }
}, 6000);

setAuthUI();
