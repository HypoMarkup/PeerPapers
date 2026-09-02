import React from "react";
import { useWebSocket } from "../context/WebSocketContext";
import { Wifi, WifiOff, LogOut, Shield } from "lucide-react";

export const Header: React.FC = () => {
  const { isConnected, snapshot, playerId, leaveRoom } = useWebSocket();

  const currentPlayer = snapshot?.players.find((p) => p.id === playerId);

  return (
    <header className="header">
      <div className="logo">
        <span>📝</span> PeerPapers
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        {snapshot && (
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Room:</span>
            <strong style={{ letterSpacing: "0.05em", color: "var(--primary)" }}>{snapshot.roomCode}</strong>
          </div>
        )}

        {currentPlayer && (
          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>{currentPlayer.name}</span>
            {currentPlayer.isAdmin && (
              <span className="badge badge-admin">
                <Shield size={12} /> Host
              </span>
            )}
          </div>
        )}

        {isConnected ? (
          <span className="badge badge-connected">
            <Wifi size={13} /> Connected
          </span>
        ) : (
          <span className="badge badge-disconnected">
            <WifiOff size={13} /> Disconnected
          </span>
        )}

        {snapshot && (
          <button className="btn btn-secondary" style={{ padding: "0.35rem 0.75rem", fontSize: "0.8rem" }} onClick={leaveRoom}>
            <LogOut size={14} /> Leave
          </button>
        )}
      </div>
    </header>
  );
};
