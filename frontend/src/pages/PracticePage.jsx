import React, { useState } from "react";
import { postJSON } from "../api";

export default function PracticePage() {
  const [userId, setUserId] = useState("user1");
  const [concept, setConcept] = useState("binary_search");
  const [mastery, setMastery] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [languageId, setLanguageId] = useState(71);
  const [loading, setLoading] = useState(false);
  const [submitLogs, setSubmitLogs] = useState({});

  const handleLoadUser = async () => {
    await postJSON("/v1/user", { user_id: userId });
  };

  const handleFetchQuestions = async () => {
    setLoading(true);
    setSubmitLogs({});
    try {
      await handleLoadUser();
      const res = await postJSON("/v1/practice", {
        user_id: userId,
        concept,
        n: 3
      });

      setMastery(res.mastery);
      setQuestions(res.questions || []);
      setAnswers({});
    } catch (err) {
      alert("Failed to fetch questions: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (qid, value) => {
    setAnswers((prev) => ({ ...prev, [qid]: value }));
  };

  const detectCodeQuestion = (q) => {
    return (
      q.type === "code" ||
      (q.testcases && q.testcases.length > 0) ||
      (q.question && q.question.toLowerCase().includes("implement")) ||
      (q.question && q.question.toLowerCase().includes("write"))
    );
  };

  const handleSubmitAnswer = async (q) => {
    const qid = q.qid;
    const ans = (answers[qid] || "").trim();
    const isCode = detectCodeQuestion(q);

    if (!ans) {
      alert(isCode ? "Please enter your code" : "Please enter your answer");
      return;
    }

    const payload = {
      user_id: userId,
      concept,
      qid
    };

    if (isCode) {
      payload.source_code = ans;
      payload.language_id = q.language_id || languageId;
    } else {
      payload.answer = ans;
    }

    try {
      const res = await postJSON("/v1/submit_answer", payload);
      setSubmitLogs((prev) => ({ ...prev, [qid]: res }));
      setMastery(res.mastery);
    } catch (err) {
      alert("Submit failed: " + err.message);
    }
  };

  const renderMastery = () => {
    if (!mastery) return null;
    const pct = Math.round((mastery.strength || 0) * 100);

    return (
      <div style={{
        padding: "0.6rem",
        background: "#020617",
        border: "1px solid #1f2937",
        borderRadius: "0.5rem",
        marginBottom: "1rem"
      }}>
        <div>Mastery for {concept}</div>
        <div style={{
          background: "#111827",
          height: "8px",
          marginTop: "6px",
          borderRadius: "999px"
        }}>
          <div style={{
            width: `${pct}%`,
            height: "8px",
            background: "#22c55e",
            borderRadius: "999px"
          }} />
        </div>
        <div style={{ marginTop: "0.4rem", color: "#9ca3af" }}>
          Strength: {pct}% • Easiness: {mastery.easiness?.toFixed(2)} • Interval: {mastery.interval} days
        </div>
      </div>
    );
  };


  return (
    <div style={{ padding: "1rem" }}>
      <h1>Practice</h1>

      {/* Controls */}
      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
        <input
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          placeholder="User ID"
        />

        <input
          value={concept}
          onChange={(e) => setConcept(e.target.value)}
          placeholder="Concept (e.g., binary_search)"
        />

        <button onClick={handleFetchQuestions}>
          {loading ? "Loading..." : "Get Questions"}
        </button>
      </div>

      {renderMastery()}

      {/* Questions */}
      {questions.map((q) => {
        const qid = q.qid;
        const log = submitLogs[qid];
        const isCode = detectCodeQuestion(q);

        return (
          <div key={qid}
            style={{
              padding: "1rem",
              marginBottom: "1rem",
              borderRadius: "0.6rem",
              background: "#020617",
              border: "1px solid #1f2937"
            }}
          >
            <div style={{ marginBottom: ".3rem", color: "#9ca3af" }}>
              Difficulty: {q.difficulty} • Type: {isCode ? "code" : "short_answer"}
            </div>

            <div style={{ marginBottom: ".6rem" }}>{q.question}</div>

            <textarea
              rows={isCode ? 8 : 3}
              value={answers[qid] || ""}
              onChange={(e) => handleAnswerChange(qid, e.target.value)}
              placeholder={isCode ? "Write your code..." : "Write your answer..."}
              style={{
                width: "100%",
                padding: "0.5rem",
                borderRadius: "0.4rem",
                background: "#111827",
                color: "#fff",
                border: "1px solid #334155"
              }}
            />

            <button
              onClick={() => handleSubmitAnswer(q)}
              style={{
                marginTop: "0.5rem",
                background: "#38bdf8",
                padding: "0.5rem 1rem",
                borderRadius: "0.3rem",
                border: "none",
                cursor: "pointer"
              }}
            >
              Submit Answer
            </button>

            {log && (
              <div style={{
                marginTop: "0.6rem",
                padding: "0.6rem",
                background: "#0f172a",
                borderRadius: "0.4rem",
                border: "1px solid #1e293b"
              }}>
                <div>Score: {log.score.toFixed(2)} | Quality: {log.quality}</div>
                <pre style={{
                  whiteSpace: "pre-wrap",
                  marginTop: "0.5rem",
                  color: "#94a3b8"
                }}>
                  {JSON.stringify(log.details, null, 2)}
                </pre>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
