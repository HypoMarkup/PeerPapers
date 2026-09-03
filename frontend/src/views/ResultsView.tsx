import React from "react";
import { useWebSocket } from "../context/WebSocketContext";
import { Trophy, Award, MessageSquare, LogOut, CheckCircle } from "lucide-react";

export const ResultsView: React.FC = () => {
  const { results, playerId, leaveRoom } = useWebSocket();

  const myResult = results.find((r) => r.player?.id === playerId);

  return (
    <div className="container" style={{ maxWidth: "900px" }}>
      {/* ─── Hero Banner ─── */}
      <div className="card" style={{ textAlign: "center", padding: "2.5rem 1.5rem" }}>
        <Trophy size={56} color="#eab308" style={{ margin: "0 auto 1rem" }} />
        <h1 style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>Exam & Peer Review Results</h1>
        <p style={{ color: "var(--text-secondary)" }}>
          All peer assessments have been completed and calculated.
        </p>

        {myResult && (
          <div
            style={{
              display: "inline-block",
              background: "var(--primary-light)",
              border: "1px solid #c7d2fe",
              borderRadius: "var(--radius)",
              padding: "1rem 2rem",
              marginTop: "1.5rem",
            }}
          >
            <span style={{ fontSize: "0.85rem", color: "var(--primary)", textTransform: "uppercase", fontWeight: 700 }}>
              Your Final Score
            </span>
            <div style={{ fontSize: "2.5rem", fontWeight: 800, color: "var(--primary)" }}>
              {myResult.totalScore} <span style={{ fontSize: "1.2rem", fontWeight: 500, color: "var(--text-secondary)" }}>/ {myResult.maxScore || 100}</span>
            </div>
          </div>
        )}
      </div>

      {/* ─── Leaderboard Card ─── */}
      <div className="card">
        <h2 style={{ fontSize: "1.25rem", marginBottom: "1.25rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Award size={22} color="var(--primary)" /> Leaderboard
        </h2>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {results.map((r, index) => {
            const isMe = r.player?.id === playerId;
            const rank = index + 1;
            const percentage = r.maxScore > 0 ? Math.round((r.totalScore / r.maxScore) * 100) : 0;

            return (
              <div
                key={r.player?.id || index}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "1rem 1.25rem",
                  borderRadius: "var(--radius)",
                  background: isMe ? "var(--primary-light)" : "var(--bg-primary)",
                  border: isMe ? "1px solid #a5b4fc" : "1px solid var(--border)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                  <span
                    style={{
                      width: "32px",
                      height: "32px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      borderRadius: "50%",
                      fontWeight: 700,
                      background: rank === 1 ? "#fef08a" : rank === 2 ? "#e2e8f0" : rank === 3 ? "#fed7aa" : "#f1f5f9",
                      color: rank === 1 ? "#854d0e" : rank === 2 ? "#475569" : rank === 3 ? "#9a3412" : "#64748b",
                    }}
                  >
                    {rank}
                  </span>

                  <div>
                    <span style={{ fontWeight: 600 }}>{r.player?.name || "Player"}</span>
                    {isMe && <span style={{ marginLeft: "0.5rem", fontSize: "0.75rem", color: "var(--primary)", fontWeight: 700 }}>(You)</span>}
                  </div>
                </div>

                <div style={{ textAlign: "right" }}>
                  <strong style={{ fontSize: "1.1rem" }}>{r.totalScore} pts</strong>
                  <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{percentage}%</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ─── Feedback Received on Your Work ─── */}
      {myResult?.feedbackReceived && (
        <div className="card">
          <h2 style={{ fontSize: "1.25rem", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <MessageSquare size={20} color="var(--primary)" /> Peer Feedback on Your Submission
          </h2>

          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {myResult.feedbackReceived.sections.map((sec) => (
              <div
                key={sec.sectionIndex}
                style={{
                  background: "var(--bg-primary)",
                  padding: "1rem",
                  borderRadius: "var(--radius)",
                  border: "1px solid var(--border)",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                  <h4 style={{ fontSize: "0.95rem", color: "var(--primary)" }}>Question {sec.sectionIndex + 1}</h4>
                  <span className="badge badge-ready">
                    <CheckCircle size={13} /> {sec.score} / {sec.maxScore}
                  </span>
                </div>
                <p style={{ fontSize: "0.9rem", color: "var(--text-primary)", whiteSpace: "pre-wrap" }}>
                  {sec.textComments || <em style={{ color: "var(--text-secondary)" }}>No written comment provided.</em>}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ─── Exit Button ─── */}
      <div style={{ textAlign: "center", marginTop: "2rem" }}>
        <button className="btn btn-secondary" onClick={leaveRoom}>
          <LogOut size={16} /> Return to Home
        </button>
      </div>
    </div>
  );
};
