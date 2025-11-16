import React, { useState } from "react";
import { getJSON, postJSON } from "../api";

export default function AdminPage() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [reindexMsg, setReindexMsg] = useState("");

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await getJSON("/admin/index/status");
      setStatus(res);
    } catch (err) {
      alert("Failed to get index status: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const triggerReindex = async () => {
    try {
      const res = await postJSON("/admin/reindex", {});
      setReindexMsg(`Reindex started at ${res.started_at}`);
    } catch (err) {
      alert("Failed to start reindex: " + err.message);
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem", marginBottom: "0.75rem" }}>Admin</h1>
      <p style={{ fontSize: "0.9rem", color: "#9ca3af", marginBottom: "1rem" }}>
        FAISS index status and manual reindex trigger.
      </p>

      <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1rem" }}>
        <button
          onClick={fetchStatus}
          disabled={loading}
          style={{
            padding: "0.45rem 0.9rem",
            borderRadius: "0.5rem",
            border: "none",
            background: loading ? "#4b5563" : "#38bdf8",
            color: "#020617",
            fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer"
          }}
        >
          {loading ? "Loading..." : "Get Index Status"}
        </button>
        <button
          onClick={triggerReindex}
          style={{
            padding: "0.45rem 0.9rem",
            borderRadius: "0.5rem",
            border: "none",
            background: "#f97316",
            color: "#020617",
            fontWeight: 600,
            cursor: "pointer"
          }}
        >
          Trigger Reindex
        </button>
      </div>

      {status && (
        <div
          style={{
            marginBottom: "0.75rem",
            padding: "0.6rem 0.7rem",
            borderRadius: "0.5rem",
            border: "1px solid #1f2937",
            background: "#020617",
            fontSize: "0.9rem"
          }}
        >
          <div>Vectors (ntotal): {status.ntotal}</div>
          <div>Dimension: {status.dim}</div>
        </div>
      )}

      {reindexMsg && (
        <div
          style={{
            padding: "0.6rem 0.7rem",
            borderRadius: "0.5rem",
            border: "1px solid #1d4ed8",
            background: "#020617",
            fontSize: "0.9rem",
            color: "#bfdbfe"
          }}
        >
          {reindexMsg}
        </div>
      )}
    </div>
  );
}
