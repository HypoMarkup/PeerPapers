import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles/index.css";
import App from "./App.tsx";
import { WebsocketProvider } from "./contexts/WebsocketProvider.tsx";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <WebsocketProvider>
      <App />
    </WebsocketProvider>
  </StrictMode>
);
