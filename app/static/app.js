"use strict";
const form = document.getElementById("greeting-form");
const output = document.getElementById("response");
async function loadHealth() {
  try {
    const res = await fetch("/api/health");
    if (!res.ok) throw new Error("Health check fallido");
    const data = await res.json();
    document.getElementById("health").textContent = `API disponible · ${data.environment}`;
    document.getElementById("release").textContent = `v${data.version} · ${data.commit.slice(0, 7)}`;
  } catch {
    document.getElementById("health").textContent = "API sin conexión";
    document.getElementById("release").textContent = "Versión no disponible";
  }
}
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = document.getElementById("send");
  button.disabled = true;
  const start = performance.now();
  try {
    const data = Object.fromEntries(new FormData(form));
    const res = await fetch("/api/saludo", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data)});
    const text = await res.text();
    const type = res.headers.get("content-type") || "";
    output.textContent = type.includes("application/json") ? JSON.stringify(JSON.parse(text), null, 2) : text;
    document.getElementById("http-status").textContent = `${res.status} · ${type.split(";")[0]}`;
    document.getElementById("duration").textContent = `${Math.round(performance.now() - start)} ms`;
  } catch {
    output.textContent = "No se pudo contactar la API. Vuelve a intentar en unos segundos.";
    document.getElementById("http-status").textContent = "ERROR DE CONEXIÓN";
  } finally { button.disabled = false; }
});
loadHealth();
