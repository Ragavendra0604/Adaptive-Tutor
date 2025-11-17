import React, { useState, useRef } from "react";
import { createChatWebSocket } from "../api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";

export default function ChatPage() {
  const [userId, setUserId] = useState("user1");
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]); 
  const [isStreaming, setIsStreaming] = useState(false);
  const wsRef = useRef(null);

  const handleSend = () => {
    if (!query.trim()) return;

    setMessages((prev) => [...prev, { role: "user", text: query }]);

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
        }

        else if (data.type === "done") {
          setIsStreaming(false);
          setMessages((prev) =>
            prev.map((m) =>
              m.role === "assistant_stream"
                ? { role: "assistant", text: m.text }
                : m
            )
          );
          ws.close();
        }

        else if (data.type === "error") {
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
        Interactive Concept Navigator
      </p>

      <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1rem", flexWrap: "wrap" }}>
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
                  : "rgba(16,185,129,0.08)"
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

            {/* ⭐ Improved Markdown Renderer */}
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: (props) => <h1 style={{ color: "#38bdf8" }} {...props} />,
                h2: (props) => <h2 style={{ color: "#67e8f9" }} {...props} />,
                h3: (props) => <h3 style={{ color: "#a5f3fc" }} {...props} />,
                p: (props) => <p style={{ margin: "0.3rem 0" }} {...props} />,
                ul: (props) => <ul style={{ marginLeft: "1.2rem" }} {...props} />,
                ol: (props) => <ol style={{ marginLeft: "1.2rem" }} {...props} />,
                blockquote: (props) => (
                  <blockquote
                    style={{
                      borderLeft: "4px solid #4b5563",
                      paddingLeft: "0.7rem",
                      opacity: 0.85,
                      margin: "0.5rem 0"
                    }}
                    {...props}
                  />
                ),
                code({ inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || "");
                  return !inline ? (
                    <SyntaxHighlighter language={match?.[1] || "text"}>
                      {String(children).replace(/\n$/, "")}
                    </SyntaxHighlighter>
                  ) : (
                    <code
                      {...props}
                      style={{
                        background: "#1e293b",
                        padding: "2px 4px",
                        borderRadius: "4px"
                      }}
                    >
                      {children}
                    </code>
                  );
                }
              }}
            >
              {m.text}
            </ReactMarkdown>
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
