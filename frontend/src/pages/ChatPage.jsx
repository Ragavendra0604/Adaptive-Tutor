import React, { useState, useRef } from "react";
import { createChatWebSocket } from "../api";

export default function ChatPage() {
  const [userId, setUserId] = useState("user1");
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]); // {role, text}
  const [isStreaming, setIsStreaming] = useState(false);
  const wsRef = useRef(null);

  const handleSend = () => {
    if (!query.trim()) return;

    // add user message
    setMessages((prev) => [...prev, { role: "user", text: query }]);

    // open WebSocket
    const ws = createChatWebSocket();
    wsRef.current = ws;
    setIsStreaming(true);

    let assistantBuffer = "";

    ws.onopen = () => {
      ws.send(JSON.stringify({ query, user_id: userId }));
      setQuery("");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "token") {
          assistantBuffer += data.text;
          // replace last assistant message live
          setMessages((prev) => {
            const clone = [...prev];
            const last = clone[clone.length - 1];
            if (last && last.role === "assistant_stream") {
              clone[clone.length - 1] = { ...last, text: assistantBuffer };
            } else {
              clone.push({ role: "assistant_stream", text: assistantBuffer });
            }
            return clone;
          });
        } else if (data.type === "done") {
          setIsStreaming(false);
          setMessages((prev) =>
            prev.map((m) =>
              m.role === "assistant_stream"
                ? { role: "assistant", text: m.text }
                : m
            )
          );
          ws.close();
        } else if (data.type === "error") {
          setIsStreaming(false);
          setMessages((prev) => [
            ...prev,
            { role: "system", text: data.message || "Error while chatting." }
          ]);
          ws.close();
        }
      } catch (err) {
        console.error("WS parse error", err);
      }
    };

    ws.onerror = () => {
      setIsStreaming(false);
      setMessages((prev) => [
        ...prev,
        { role: "system", text: "WebSocket error" }
      ]);
    };

    ws.onclose = () => {
      setIsStreaming(false);
    };
  };

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem", marginBottom: "0.75rem" }}>Chat Tutor</h1>
      <p style={{ fontSize: "0.9rem", color: "#9ca3af", marginBottom: "1.5rem" }}>
        Ask DSA doubts. Backend uses your RAG + OpenRouter / fallback summarizer.
      </p>

      <div
        style={{
          display: "flex",
          gap: "0.75rem",
          marginBottom: "1rem",
          flexWrap: "wrap"
        }}
      >
        <div>
          <label style={{ fontSize: "0.8rem", color: "#9ca3af" }}>User ID</label>
          <input
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            style={{
              padding: "0.4rem 0.6rem",
              borderRadius: "0.35rem",
              border: "1px solid #4b5563",
              background: "#020617",
              color: "#e5e7eb",
              marginLeft: "0.5rem"
            }}
          />
        </div>
      </div>

      <div
        style={{
          border: "1px solid #1f2937",
          borderRadius: "0.5rem",
          padding: "0.75rem",
          marginBottom: "0.75rem",
          background: "#020617",
          height: "350px",
          overflowY: "auto"
        }}
      >
        {messages.length === 0 && (
          <div style={{ color: "#6b7280", fontSize: "0.9rem" }}>
            Start by asking something like:
            <br />
            <code style={{ fontSize: "0.85rem" }}>
              &quot;Explain BFS with example&quot;
            </code>
          </div>
        )}
        {messages.map((m, idx) => (
          <div
            key={idx}
            style={{
              marginBottom: "0.6rem",
              padding: "0.5rem 0.6rem",
              borderRadius: "0.4rem",
              background:
                m.role === "user"
                  ? "rgba(59,130,246,0.1)"
                  : m.role === "assistant" || m.role === "assistant_stream"
                  ? "rgba(16,185,129,0.08)"
                  : "rgba(148,163,184,0.1)"
            }}
          >
            <div
              style={{
                fontSize: "0.75rem",
                marginBottom: "0.25rem",
                color: "#9ca3af",
                textTransform: "uppercase"
              }}
            >
              {m.role}
            </div>
            <div style={{ fontSize: "0.9rem", whiteSpace: "pre-wrap" }}>
              {m.text}
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: "0.5rem" }}>
        <textarea
          rows={2}
          placeholder="Type your DSA question here..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{
            flex: 1,
            padding: "0.6rem 0.7rem",
            borderRadius: "0.5rem",
            border: "1px solid #4b5563",
            background: "#020617",
            color: "#e5e7eb",
            resize: "none"
          }}
        />
        <button
          onClick={handleSend}
          disabled={isStreaming}
          style={{
            padding: "0 1rem",
            borderRadius: "0.5rem",
            border: "none",
            background: isStreaming ? "#4b5563" : "#38bdf8",
            color: "#020617",
            fontWeight: 600,
            cursor: isStreaming ? "not-allowed" : "pointer"
          }}
        >
          {isStreaming ? "Streaming..." : "Send"}
        </button>
      </div>
    </div>
  );
}
