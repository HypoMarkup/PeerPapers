import React from "react";
import { AlertCircle, X } from "lucide-react";
import { useWebSocket } from "../context/WebSocketContext";

export const ErrorMessage: React.FC = () => {
  const { errorMessage, clearError } = useWebSocket();

  if (!errorMessage) return null;

  return (
    <div className="alert-error">
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <AlertCircle size={18} />
        <span>{errorMessage}</span>
      </div>
      <button
        onClick={clearError}
        style={{
          background: "none",
          border: "none",
          color: "inherit",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
        }}
      >
        <X size={16} />
      </button>
    </div>
  );
};
