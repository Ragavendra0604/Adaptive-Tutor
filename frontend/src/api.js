const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function postJSON(path, body) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Error ${res.status}`);
  }
  return res.json();
}

export async function getJSON(path) {
  const res = await fetch(`${API_BASE_URL}${path}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Error ${res.status}`);
  }
  return res.json();
}

export function createChatWebSocket() {
  // ws:// or wss:// based on API_BASE_URL
  const url = new URL(API_BASE_URL);
  const wsProtocol = url.protocol === "https:" ? "wss:" : "ws:";
  const wsBase = `${wsProtocol}//${url.host}`;
  return new WebSocket(`${wsBase}/v1/ws/chat`);
}
