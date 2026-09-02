import React from "react";
import { useWebSocket } from "./context/WebSocketContext";
import { Header } from "./components/Header";
import { ErrorMessage } from "./components/ErrorMessage";
import { AuthView } from "./views/AuthView";
import { LobbyView } from "./views/LobbyView";
import { ExamView } from "./views/ExamView";
import { MarkingView } from "./views/MarkingView";
import { ResultsView } from "./views/ResultsView";
import { RoomState } from "./generated/v1/models_pb";

export const App: React.FC = () => {
  const { snapshot } = useWebSocket();

  const renderCurrentView = () => {
    if (!snapshot) {
      return <AuthView />;
    }

    switch (snapshot.state) {
      case RoomState.LOBBY:
        return <LobbyView />;
      case RoomState.EXAM:
        return <ExamView />;
      case RoomState.MARKING:
        return <MarkingView />;
      case RoomState.RESULTS:
        return <ResultsView />;
      default:
        return <AuthView />;
    }
  };

  return (
    <div>
      <Header />
      <div className="container">
        <ErrorMessage />
        {renderCurrentView()}
      </div>
    </div>
  );
};
