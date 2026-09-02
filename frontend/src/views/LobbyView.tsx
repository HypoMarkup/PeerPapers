import React, { useState } from "react";
import { useWebSocket } from "../context/WebSocketContext";
import { Copy, Check, Upload, Play, CheckCircle2, XCircle, FileText, Settings, User } from "lucide-react";

export const LobbyView: React.FC = () => {
  const { snapshot, playerId, setReady, uploadExam, updateSettings, startExam } = useWebSocket();
  const [copied, setCopied] = useState(false);
  const [newDuration, setNewDuration] = useState(snapshot?.settings?.examDurationMins || 15);

  if (!snapshot) return null;

  const currentPlayer = snapshot.players.find((p) => p.id === playerId);
  const isAdmin = currentPlayer?.isAdmin ?? false;
  const allReady = snapshot.players.length > 0 && snapshot.players.every((p) => p.isReady);
  const canStart = isAdmin && allReady && snapshot.examPdfUploaded;

  const copyCode = () => {
    navigator.clipboard.writeText(snapshot.roomCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      const buffer = reader.result as ArrayBuffer;
      uploadExam(file.name, new Uint8Array(buffer));
    };
    reader.readAsArrayBuffer(file);
  };

  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    if (newDuration > 0) {
      updateSettings(newDuration);
    }
  };

  return (
    <div className="container">
      {/* ─── Room Code Banner ─── */}
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 700 }}>
            Room Code
          </span>
          <h1 style={{ fontSize: "2.2rem", letterSpacing: "0.1em", color: "var(--primary)" }}>{snapshot.roomCode}</h1>
        </div>

        <button className="btn btn-secondary" onClick={copyCode}>
          {copied ? <Check size={16} color="var(--success)" /> : <Copy size={16} />}
          {copied ? "Copied!" : "Copy Code"}
        </button>
      </div>

      <div className="grid-2">
        {/* ─── Left Column: Player List ─── */}
        <div className="card">
          <h2 style={{ fontSize: "1.2rem", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <User size={20} /> Players ({snapshot.players.length})
          </h2>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {snapshot.players.map((player) => {
              const isMe = player.id === playerId;
              return (
                <div
                  key={player.id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "0.75rem 1rem",
                    background: isMe ? "var(--primary-light)" : "var(--bg-primary)",
                    borderRadius: "var(--radius)",
                    border: isMe ? "1px solid #c7d2fe" : "1px solid var(--border)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <span style={{ fontWeight: 600 }}>{player.name}</span>
                    {isMe && <span style={{ fontSize: "0.75rem", color: "var(--primary)" }}>(You)</span>}
                    {player.isAdmin && <span className="badge badge-admin">Host</span>}
                  </div>

                  <div>
                    {player.isReady ? (
                      <span className="badge badge-ready">
                        <CheckCircle2 size={13} /> Ready
                      </span>
                    ) : (
                      <span className="badge badge-not-ready">
                        <XCircle size={13} /> Not Ready
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{ marginTop: "1.5rem" }}>
            <button
              className={`btn ${currentPlayer?.isReady ? "btn-secondary" : "btn-primary"}`}
              style={{ width: "100%" }}
              onClick={() => setReady(!currentPlayer?.isReady)}
            >
              {currentPlayer?.isReady ? "Cancel Ready" : "I am Ready!"}
            </button>
          </div>
        </div>

        {/* ─── Right Column: Exam Details & Host Controls ─── */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Exam Status Card */}
          <div className="card">
            <h2 style={{ fontSize: "1.2rem", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <FileText size={20} /> Exam Paper
            </h2>

            <div style={{ marginBottom: "1rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
                <span>Status:</span>
                {snapshot.examPdfUploaded ? (
                  <span className="badge badge-ready">
                    <CheckCircle2 size={13} /> PDF Uploaded
                  </span>
                ) : (
                  <span className="badge badge-disconnected">No PDF Uploaded Yet</span>
                )}
              </div>
              <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                Exam Duration: <strong>{snapshot.settings?.examDurationMins || 15} minutes</strong>
              </p>
            </div>

            {isAdmin && (
              <div>
                <label className="btn btn-secondary" style={{ width: "100%", cursor: "pointer" }}>
                  <Upload size={16} /> Upload Exam PDF
                  <input type="file" accept="application/pdf" style={{ display: "none" }} onChange={handleFileUpload} />
                </label>
              </div>
            )}
          </div>

          {/* Admin Settings & Start Controls */}
          {isAdmin && (
            <div className="card">
              <h2 style={{ fontSize: "1.2rem", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Settings size={20} /> Host Controls
              </h2>

              <form onSubmit={handleSaveSettings} style={{ marginBottom: "1.5rem" }}>
                <div className="form-group">
                  <label className="form-label">Change Duration (minutes)</label>
                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    <input
                      className="form-input"
                      type="number"
                      min={1}
                      max={180}
                      value={newDuration}
                      onChange={(e) => setNewDuration(Number(e.target.value))}
                    />
                    <button type="submit" className="btn btn-secondary">
                      Update
                    </button>
                  </div>
                </div>
              </form>

              <button
                className="btn btn-primary"
                style={{ width: "100%", padding: "0.85rem", fontSize: "1.05rem" }}
                disabled={!canStart}
                onClick={startExam}
              >
                <Play size={18} /> Start Exam
              </button>

              {!canStart && (
                <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "0.5rem", textAlign: "center" }}>
                  {!snapshot.examPdfUploaded ? "• Exam PDF must be uploaded" : "• All players must be marked ready to start"}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
