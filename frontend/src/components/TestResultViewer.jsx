import React, { useState } from "react";

export const TestResultViewer = ({ result }) => {
  const [activeTab, setActiveTab] = useState(0);

  if (!result || !result.details) return null;

  const { score, quality, details } = result;
  const testcases = details.testcases || [];

  const compileError = details.judge_raw?.stderr || details.judge_raw?.compile_output;
  
  const isPass = score === 1.0;

  // If there was a compilation/runtime error that prevented test cases from running
  if (testcases.length === 0 && compileError) {
    return (
      <div style={styles.container}>
        <div style={{ ...styles.headerBar, color: "#ef4444", justifyContent: "flex-start" }}>
           <span style={{ fontWeight: "bold" }}>Runtime / Compilation Error</span>
        </div>
        {/* FIX: Removed atob() to prevent crashing on plain text */}
        <div style={styles.errorBox}>{compileError}</div>
      </div>
    );
  }

  const currentCase = testcases[activeTab];

  return (
    <div style={styles.container}>
      {/* Header: Status & Score */}
      <div style={styles.headerBar}>
        <span style={{ 
          fontWeight: "bold", 
          fontSize: "1.1rem",
          color: isPass ? "#22c55e" : "#ef4444" 
        }}>
          {isPass ? "Accepted" : "Wrong Answer"}
        </span>
        <span style={{ color: "#9ca3af", fontSize: "0.9rem" }}>
          Runtime: {details.judge_raw?.time || "0"}s
        </span>
      </div>

      {/* Tabs for Cases */}
      <div style={styles.tabBar}>
        {testcases.map((tc, idx) => (
          <button
            key={idx}
            onClick={() => setActiveTab(idx)}
            style={{
              ...styles.tab,
              ...(activeTab === idx ? styles.activeTab : {}),
              color: tc.passed ? "#22c55e" : "#ef4444" 
            }}
          >
             Case {idx + 1}
          </button>
        ))}
      </div>

      {/* Case Details */}
      {currentCase && (
        <div style={styles.caseContent}>
          <Label text="Input =" />
          <CodeBox content={currentCase.stdin} />

          <Label text="Output =" />
          <CodeBox content={currentCase.stdout || "(No output)"} />

          <Label text="Expected =" />
          <CodeBox content={currentCase.expected} />

          {/* Only show error if this specific case failed and has stderr */}
          {!currentCase.passed && currentCase.stderr && (
            <>
              <Label text="Error Output =" />
              <div style={{...styles.codeBox, color: "#ef4444", borderColor: "#ef4444"}}>
                {currentCase.stderr}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

// --- Sub Components ---
const Label = ({ text }) => (
  <div style={{ color: "#9ca3af", fontSize: "0.85rem", marginTop: "1rem", marginBottom: "0.25rem" }}>
    {text}
  </div>
);

const CodeBox = ({ content }) => (
  <div style={styles.codeBox}>{content}</div>
);

// --- Styles ---
const styles = {
  container: {
    marginTop: "1rem",
    background: "#1e293b",
    borderRadius: "0.5rem",
    border: "1px solid #334155",
    overflow: "hidden",
    fontFamily: "sans-serif"
  },
  headerBar: {
    padding: "1rem",
    borderBottom: "1px solid #334155",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    background: "#0f172a"
  },
  tabBar: {
    display: "flex",
    background: "#1e293b",
    borderBottom: "1px solid #334155",
    overflowX: "auto" // handle many test cases
  },
  tab: {
    padding: "0.75rem 1.5rem",
    background: "transparent",
    border: "none",
    color: "#64748b",
    cursor: "pointer",
    fontSize: "0.9rem",
    borderBottom: "2px solid transparent",
    transition: "all 0.2s",
    whiteSpace: "nowrap"
  },
  activeTab: {
    color: "#f8fafc",
    borderBottom: "2px solid #f8fafc",
    background: "rgba(255,255,255,0.05)"
  },
  caseContent: {
    padding: "1rem",
    background: "#0f172a"
  },
  codeBox: {
    background: "#1e293b",
    padding: "0.75rem",
    borderRadius: "0.375rem",
    fontFamily: "monospace",
    fontSize: "0.9rem",
    color: "#e2e8f0",
    border: "1px solid #334155",
    whiteSpace: "pre-wrap",
    wordBreak: "break-all"
  },
  errorBox: {
    padding: "1rem",
    color: "#f87171",
    fontFamily: "monospace",
    whiteSpace: "pre-wrap",
    background: "#0f172a"
  }
};