import React, { useState } from "react";
import { useWebSocket } from "../context/WebSocketContext";
import { Timer } from "../components/Timer";
import { Whiteboard } from "../components/Whiteboard";
import { SubmissionSection } from "../generated/v1/models_pb";
import { CheckSquare, AlertTriangle, Send, UserCheck, Clock } from "lucide-react";

export const MarkingView: React.FC = () => {
  const { snapshot, playerId, assignedPaper, submitMarking, forceEndPhase } = useWebSocket();
  const [submitted, setSubmitted] = useState(false);

  const currentPlayer = snapshot?.players.find((p) => p.id === playerId);
  const isAdmin = currentPlayer?.isAdmin ?? false;

  const sections: SubmissionSection[] = assignedPaper?.submission?.sections ?? [];
  const items: { sectionIndex: number }[] = sections.length > 0 ? sections : [{ sectionIndex: 0 }];

  // Form State for per-section scores and comments
  const [grades, setGrades] = useState<{ [key: number]: { score: number; maxScore: number; textComments: string } }>({
    0: { score: 100, maxScore: 100, textComments: "" },
  });

  const handleScoreChange = (idx: number, score: number) => {
    setGrades((prev) => ({
      ...prev,
      [idx]: {
        score,
        maxScore: prev[idx]?.maxScore || 100,
        textComments: prev[idx]?.textComments || "",
      },
    }));
  };

  const handleCommentChange = (idx: number, textComments: string) => {
    setGrades((prev) => ({
      ...prev,
      [idx]: {
        score: prev[idx]?.score ?? 100,
        maxScore: prev[idx]?.maxScore || 100,
        textComments,
      },
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const resultList = items.map((s) => ({
      sectionIndex: s.sectionIndex,
      score: grades[s.sectionIndex]?.score ?? 100,
      maxScore: grades[s.sectionIndex]?.maxScore ?? 100,
      textComments: grades[s.sectionIndex]?.textComments ?? "",
    }));

    submitMarking(resultList);
    setSubmitted(true);
  };

  if (!assignedPaper) {
    return (
      <div className="container" style={{ textAlign: "center", marginTop: "4rem" }}>
        <div className="card" style={{ maxWidth: "500px", margin: "0 auto", padding: "2.5rem" }}>
          <Clock size={48} color="var(--primary)" style={{ margin: "0 auto 1rem" }} />
          <h2>Preparing Peer Assignments...</h2>
          <p style={{ color: "var(--text-secondary)", marginTop: "0.5rem" }}>
            The server is distributing submissions to reviewers.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container" style={{ maxWidth: "1500px" }}>
      {/* ─── Top Bar ─── */}
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.75rem 1.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <CheckSquare size={22} color="var(--primary)" />
          <h2 style={{ fontSize: "1.25rem" }}>
            Peer Review: Grading <strong>{assignedPaper.authorName}</strong>
          </h2>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          {snapshot && <Timer phaseEndTime={snapshot.phaseEndTime} />}

          {isAdmin && (
            <button className="btn btn-danger" style={{ fontSize: "0.85rem" }} onClick={forceEndPhase}>
              <AlertTriangle size={14} /> End Marking Early
            </button>
          )}
        </div>
      </div>

      {/* ─── Split Screen: Student Submission on Left, Marking Form on Right ─── */}
      <div className="split-view">
        {/* Left Pane: Student Submission */}
        <div className="card" style={{ overflowY: "auto", display: "flex", flexDirection: "column" }}>
          <h3 style={{ fontSize: "1.05rem", marginBottom: "1rem", borderBottom: "1px solid var(--border)", paddingBottom: "0.5rem" }}>
            📄 {assignedPaper.authorName}'s Answers
          </h3>

          {sections.length > 0 ? (
            sections.map((sec) => (
              <div key={sec.sectionIndex} style={{ marginBottom: "2rem", paddingBottom: "1.5rem", borderBottom: "1px solid var(--border)" }}>
                <h4 style={{ fontSize: "0.95rem", color: "var(--primary)", marginBottom: "0.75rem" }}>
                  Section {sec.sectionIndex + 1}
                </h4>

                <div style={{ marginBottom: "1rem" }}>
                  <label className="form-label" style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                    Written Text:
                  </label>
                  <div
                    style={{
                      background: "var(--bg-primary)",
                      padding: "0.85rem 1rem",
                      borderRadius: "var(--radius)",
                      border: "1px solid var(--border)",
                      whiteSpace: "pre-wrap",
                      minHeight: "80px",
                    }}
                  >
                    {sec.textData || <em style={{ color: "var(--text-secondary)" }}>No text answer provided.</em>}
                  </div>
                </div>

                {sec.whiteboardData && (
                  <div>
                    <label className="form-label" style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                      🎨 Whiteboard Diagram:
                    </label>
                    <Whiteboard key={`marking-wb-${sec.sectionIndex}`} initialData={sec.whiteboardData} viewModeEnabled={true} height="350px" />
                  </div>
                )}
              </div>
            ))
          ) : (
            <p style={{ color: "var(--text-secondary)" }}>No written answers were submitted for this paper.</p>
          )}
        </div>

        {/* Right Pane: Grading & Feedback Form */}
        <div className="card" style={{ display: "flex", flexDirection: "column" }}>
          <h3 style={{ fontSize: "1.05rem", marginBottom: "1rem", borderBottom: "1px solid var(--border)", paddingBottom: "0.5rem" }}>
            ✏️ Your Assessment
          </h3>

          {submitted ? (
            <div style={{ textAlign: "center", padding: "3rem 1rem", margin: "auto" }}>
              <UserCheck size={48} color="var(--success)" style={{ margin: "0 auto 1rem" }} />
              <h3>Marks Submitted!</h3>
              <p style={{ color: "var(--text-secondary)", marginTop: "0.5rem" }}>
                Waiting for the other peer reviewers to finish their assessments...
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", flex: 1 }}>
              <div style={{ flex: 1, overflowY: "auto" }}>
                {items.map((sec) => {
                  const idx = sec.sectionIndex;
                  return (
                    <div key={idx} style={{ marginBottom: "1.5rem", padding: "1rem", background: "var(--bg-primary)", borderRadius: "var(--radius)", border: "1px solid var(--border)" }}>
                      <h4 style={{ fontSize: "0.95rem", marginBottom: "0.75rem" }}>
                        Section {idx + 1} Evaluation
                      </h4>

                      <div className="form-group">
                        <label className="form-label">Score (out of 100):</label>
                        <input
                          className="form-input"
                          type="number"
                          min={0}
                          max={100}
                          value={grades[idx]?.score ?? 100}
                          onChange={(e) => handleScoreChange(idx, Number(e.target.value))}
                          required
                        />
                      </div>

                      <div className="form-group" style={{ marginBottom: 0 }}>
                        <label className="form-label">Constructive Feedback / Comments:</label>
                        <textarea
                          className="form-textarea"
                          style={{ minHeight: "80px" }}
                          placeholder="Provide helpful feedback or point out mistakes..."
                          value={grades[idx]?.textComments ?? ""}
                          onChange={(e) => handleCommentChange(idx, e.target.value)}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: "1rem", padding: "0.75rem" }}>
                <Send size={16} /> Submit Marks & Feedback
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
