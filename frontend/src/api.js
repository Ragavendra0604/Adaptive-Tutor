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

export const createChatWebSocket = () => {
  let url = import.meta.env.VITE_API_URL || "http://localhost:8000";

  url = url.replace(/^http/, "ws");

  if (url.endsWith("/")) {
    url = url.slice(0, -1);
  }
  
  const wsUrl = `${url}/v1/ws/chat`;

  console.log("Connecting to WebSocket:", wsUrl); // log
  return new WebSocket(wsUrl);
};
