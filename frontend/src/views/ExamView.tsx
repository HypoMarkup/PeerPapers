import React, { useEffect, useState, useRef } from "react";
import { useWebSocket } from "../context/WebSocketContext";
import { Timer } from "../components/Timer";
import { Whiteboard } from "../components/Whiteboard";
import { FileText, Save, CheckCircle2, AlertTriangle, Plus, Trash2, Edit3, Palette } from "lucide-react";

export const ExamView: React.FC = () => {
  const { snapshot, playerId, pdfBlobUrl, requestExamPdf, saveProgress, forceEndPhase } = useWebSocket();
  const [sectionTexts, setSectionTexts] = useState<{ [key: number]: string }>({ 0: "" });
  const [sectionWhiteboards, setSectionWhiteboards] = useState<{ [key: number]: string }>({ 0: "" });
  const [activeSection, setActiveSection] = useState(0);
  const [activeTab, setActiveTab] = useState<"text" | "whiteboard">("text");

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

  const triggerAutosave = (sectionIndex: number, text: string, wb: string) => {
    setIsSaving(true);

    if (debounceTimers.current[sectionIndex]) {
      clearTimeout(debounceTimers.current[sectionIndex]);
    }

    debounceTimers.current[sectionIndex] = setTimeout(() => {
      saveProgress(sectionIndex, text, wb);
      setIsSaving(false);
      setLastSaved(new Date());
    }, 1200);
  };

  const handleTextChange = (sectionIndex: number, text: string) => {
    setSectionTexts((prev) => ({ ...prev, [sectionIndex]: text }));
    triggerAutosave(sectionIndex, text, sectionWhiteboards[sectionIndex] || "");
  };

  const handleWhiteboardChange = (sectionIndex: number, wbJson: string) => {
    setSectionWhiteboards((prev) => ({ ...prev, [sectionIndex]: wbJson }));
    triggerAutosave(sectionIndex, sectionTexts[sectionIndex] || "", wbJson);
  };

  const addSection = () => {
    const nextIdx = Math.max(...Object.keys(sectionTexts).map(Number), -1) + 1;
    setSectionTexts((prev) => ({ ...prev, [nextIdx]: "" }));
    setSectionWhiteboards((prev) => ({ ...prev, [nextIdx]: "" }));
    setActiveSection(nextIdx);
  };

  const removeSection = (idx: number) => {
    if (Object.keys(sectionTexts).length <= 1) return;
    setSectionTexts((prev) => {
      const copy = { ...prev };
      delete copy[idx];
      return copy;
    });
    setSectionWhiteboards((prev) => {
      const copy = { ...prev };
      delete copy[idx];
      return copy;
    });
    const remaining = Object.keys(sectionTexts).map(Number).filter((k) => k !== idx);
    setActiveSection(remaining[0] ?? 0);
  };

  return (
    <div className="container" style={{ maxWidth: "1500px" }}>
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

      {/* ─── Split Screen: PDF on Left, Multi-Section Workspace on Right ─── */}
      <div className="split-view">
        {/* Left Pane: PDF Viewer */}
        <div className="card" style={{ padding: "0.5rem", overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <div style={{ padding: "0.5rem 1rem", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <FileText size={18} color="var(--primary)" />
            <strong style={{ fontSize: "0.95rem" }}>Exam Questions</strong>
          </div>

          <div style={{ flex: 1, height: "100%", minHeight: "550px", background: "#525659" }}>
            {pdfBlobUrl ? (
              <iframe src={pdfBlobUrl} title="Exam Paper" style={{ width: "100%", height: "100%", border: "none" }} />
            ) : (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#ffffff" }}>
                Loading Exam PDF...
              </div>
            )}
          </div>
        </div>

        {/* Right Pane: Student Answer Workspace */}
        <div className="card" style={{ display: "flex", flexDirection: "column" }}>
          {/* Top Section Tabs */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: "1px solid var(--border)", paddingBottom: "0.75rem", marginBottom: "1rem", flexWrap: "wrap", gap: "0.5rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", overflowX: "auto" }}>
              {Object.keys(sectionTexts).map((key) => {
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
                    {Object.keys(sectionTexts).length > 1 && (
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

            {/* Sub-tab Switcher: Text vs Whiteboard */}
            <div style={{ display: "flex", background: "#f1f5f9", padding: "0.2rem", borderRadius: "var(--radius)" }}>
              <button
                className="btn"
                style={{
                  padding: "0.3rem 0.75rem",
                  fontSize: "0.8rem",
                  background: activeTab === "text" ? "#ffffff" : "transparent",
                  color: activeTab === "text" ? "var(--primary)" : "var(--text-secondary)",
                  boxShadow: activeTab === "text" ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
                }}
                onClick={() => setActiveTab("text")}
              >
                <Edit3 size={13} /> Text Answer
              </button>
              <button
                className="btn"
                style={{
                  padding: "0.3rem 0.75rem",
                  fontSize: "0.8rem",
                  background: activeTab === "whiteboard" ? "#ffffff" : "transparent",
                  color: activeTab === "whiteboard" ? "var(--primary)" : "var(--text-secondary)",
                  boxShadow: activeTab === "whiteboard" ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
                }}
                onClick={() => setActiveTab("whiteboard")}
              >
                <Palette size={13} /> Whiteboard Diagram
              </button>
            </div>
          </div>

          {/* Section Content Area */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            {activeTab === "text" ? (
              <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
                <label className="form-label">Written Answer for Section {activeSection + 1}:</label>
                <textarea
                  className="form-textarea"
                  style={{ flex: 1, minHeight: "450px" }}
                  placeholder="Type your answer, working, formulas, and explanations here (autosaved)..."
                  value={sectionTexts[activeSection] || ""}
                  onChange={(e) => handleTextChange(activeSection, e.target.value)}
                />
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
                <label className="form-label">Excalidraw Whiteboard for Section {activeSection + 1}:</label>
                <Whiteboard
                  key={`wb-${activeSection}`}
                  initialData={sectionWhiteboards[activeSection]}
                  onChange={(data) => handleWhiteboardChange(activeSection, data)}
                  height="450px"
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
