import React, { useState } from "react";
import { useWebSocket } from "../context/WebSocketContext";
import { PlusCircle, LogIn } from "lucide-react";

export const AuthView: React.FC = () => {
  const { createRoom, joinRoom } = useWebSocket();
  const [activeTab, setActiveTab] = useState<"create" | "join">("create");

  // Create Form State
  const [createName, setCreateName] = useState("");
  const [createPassword, setCreatePassword] = useState("");
  const [durationMins, setDurationMins] = useState(15);

  // Join Form State
  const [joinCode, setJoinCode] = useState("");
  const [joinName, setJoinName] = useState("");
  const [joinPassword, setJoinPassword] = useState("");

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!createName.trim() || !createPassword.trim()) return;
    createRoom(createName.trim(), createPassword.trim(), durationMins);
  };

  const handleJoin = (e: React.FormEvent) => {
    e.preventDefault();
    if (!joinCode.trim() || !joinName.trim() || !joinPassword.trim()) return;
    joinRoom(joinCode.trim().toUpperCase(), joinName.trim(), joinPassword.trim());
  };

  return (
    <div style={{ maxWidth: "480px", margin: "3rem auto" }}>
      <div className="card">
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem", borderBottom: "1px solid var(--border)", paddingBottom: "0.75rem" }}>
          <button
            className={`btn ${activeTab === "create" ? "btn-primary" : "btn-secondary"}`}
            style={{ flex: 1 }}
            onClick={() => setActiveTab("create")}
          >
            <PlusCircle size={16} /> Create Room
          </button>
          <button
            className={`btn ${activeTab === "join" ? "btn-primary" : "btn-secondary"}`}
            style={{ flex: 1 }}
            onClick={() => setActiveTab("join")}
          >
            <LogIn size={16} /> Join Room
          </button>
        </div>

        {activeTab === "create" ? (
          <form onSubmit={handleCreate}>
            <div className="form-group">
              <label className="form-label">Your Name</label>
              <input
                className="form-input"
                type="text"
                placeholder="e.g. Alice"
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Room Password</label>
              <input
                className="form-input"
                type="password"
                placeholder="Set a password for your room"
                value={createPassword}
                onChange={(e) => setCreatePassword(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Exam Duration (minutes)</label>
              <input
                className="form-input"
                type="number"
                min={1}
                max={180}
                value={durationMins}
                onChange={(e) => setDurationMins(Number(e.target.value))}
                required
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: "0.5rem" }}>
              Create Exam Room
            </button>
          </form>
        ) : (
          <form onSubmit={handleJoin}>
            <div className="form-group">
              <label className="form-label">6-Character Room Code</label>
              <input
                className="form-input"
                type="text"
                maxLength={6}
                placeholder="e.g. WQPWPF"
                style={{ textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 700 }}
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Your Name</label>
              <input
                className="form-input"
                type="text"
                placeholder="e.g. Bob"
                value={joinName}
                onChange={(e) => setJoinName(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Room Password</label>
              <input
                className="form-input"
                type="password"
                placeholder="Enter room password"
                value={joinPassword}
                onChange={(e) => setJoinPassword(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: "0.5rem" }}>
              Join Exam Room
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
