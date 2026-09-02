import React, { useEffect, useState, useRef } from "react";
import { useWebSocket } from "../context/WebSocketContext";
import { Timer } from "../components/Timer";
import { FileText, Save, CheckCircle2, AlertTriangle, Plus, Trash2 } from "lucide-react";

export const ExamView: React.FC = () => {
  const { snapshot, playerId, pdfBlobUrl, requestExamPdf, saveProgress, forceEndPhase } = useWebSocket();
  const [sections, setSections] = useState<{ [key: number]: string }>({ 0: "" });
  const [activeSection, setActiveSection] = useState(0);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const debounceTimers = useRef<{ [key: number]: ReturnType<typeof setTimeout> }>({});

  const currentPlayer = snapshot?.players.find((p) => p.id === playerId);
  const isAdmin = currentPlayer?.isAdmin ?? false;

  // Request PDF on mount if not yet received
  useEffect(() => {
    if (!pdfBlobUrl) {
      requestExamPdf();
    }
  }, [pdfBlobUrl, requestExamPdf]);

  const handleTextChange = (sectionIndex: number, text: string) => {
    setSections((prev) => ({ ...prev, [sectionIndex]: text }));
    setIsSaving(true);

    if (debounceTimers.current[sectionIndex]) {
      clearTimeout(debounceTimers.current[sectionIndex]);
    }

    debounceTimers.current[sectionIndex] = setTimeout(() => {
      saveProgress(sectionIndex, text);
      setIsSaving(false);
      setLastSaved(new Date());
    }, 1200);
  };

  const addSection = () => {
    const nextIdx = Math.max(...Object.keys(sections).map(Number), -1) + 1;
    setSections((prev) => ({ ...prev, [nextIdx]: "" }));
    setActiveSection(nextIdx);
  };

  const removeSection = (idx: number) => {
    if (Object.keys(sections).length <= 1) return;
    setSections((prev) => {
      const copy = { ...prev };
      delete copy[idx];
      return copy;
    });
    const remaining = Object.keys(sections).map(Number).filter((k) => k !== idx);
    setActiveSection(remaining[0] ?? 0);
  };

  return (
    <div className="container" style={{ maxWidth: "1400px" }}>
      {/* ─── Top Bar: Exam Title, Timer, and Admin End Phase ─── */}
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.75rem 1.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <h2 style={{ fontSize: "1.25rem", color: "var(--primary)" }}>Exam in Progress</h2>
          {isSaving ? (
            <span style={{ fontSize: "0.8rem", color: "var(--warning)", display: "flex", alignItems: "center", gap: "0.3rem" }}>
              <Save size={14} /> Autosaving...
            </span>
          ) : lastSaved ? (
            <span style={{ fontSize: "0.8rem", color: "var(--success)", display: "flex", alignItems: "center", gap: "0.3rem" }}>
              <CheckCircle2 size={14} /> Saved
            </span>
          ) : null}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          {snapshot && <Timer phaseEndTime={snapshot.phaseEndTime} />}

          {isAdmin && (
            <button className="btn btn-danger" style={{ fontSize: "0.85rem" }} onClick={forceEndPhase}>
              <AlertTriangle size={14} /> End Exam Early
            </button>
          )}
        </div>
      </div>

      {/* ─── Split Screen: PDF on Left, Answer Workspace on Right ─── */}
      <div className="split-view">
        {/* Left Pane: PDF Viewer */}
        <div className="card" style={{ padding: "0.5rem", overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <div style={{ padding: "0.5rem 1rem", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <FileText size={18} color="var(--primary)" />
            <strong style={{ fontSize: "0.95rem" }}>Exam Questions</strong>
          </div>

          <div style={{ flex: 1, height: "100%", minHeight: "500px", background: "#525659" }}>
            {pdfBlobUrl ? (
              <iframe src={pdfBlobUrl} title="Exam Paper" style={{ width: "100%", height: "100%", border: "none" }} />
            ) : (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#ffffff" }}>
                Loading Exam PDF...
              </div>
            )}
          </div>
        </div>

        {/* Right Pane: Student Answer Editor */}
        <div className="card" style={{ display: "flex", flexDirection: "column" }}>
          {/* Section Tabs */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", borderBottom: "1px solid var(--border)", paddingBottom: "0.75rem", marginBottom: "1rem", overflowX: "auto" }}>
            {Object.keys(sections).map((key) => {
              const idx = Number(key);
              const isActive = idx === activeSection;
              return (
                <div key={idx} style={{ display: "flex", alignItems: "center" }}>
                  <button
                    className={`btn ${isActive ? "btn-primary" : "btn-secondary"}`}
                    style={{ padding: "0.4rem 0.8rem", fontSize: "0.85rem" }}
                    onClick={() => setActiveSection(idx)}
                  >
                    Section {idx + 1}
                  </button>
                  {Object.keys(sections).length > 1 && (
                    <button
                      onClick={() => removeSection(idx)}
                      style={{ background: "none", border: "none", color: "var(--text-secondary)", cursor: "pointer", marginLeft: "-0.5rem", padding: "0.2rem" }}
                      title="Delete Section"
                    >
                      <Trash2 size={12} />
                    </button>
                  )}
                </div>
              );
            })}

            <button className="btn btn-secondary" style={{ padding: "0.4rem 0.6rem" }} onClick={addSection} title="Add Section">
              <Plus size={14} />
            </button>
          </div>

          {/* Section Content Area */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <label className="form-label">Answer for Section {activeSection + 1}:</label>
            <textarea
              className="form-textarea"
              style={{ flex: 1, minHeight: "380px" }}
              placeholder="Type your answer, working, and explanations here (automatically saved)..."
              value={sections[activeSection] || ""}
              onChange={(e) => handleTextChange(activeSection, e.target.value)}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
