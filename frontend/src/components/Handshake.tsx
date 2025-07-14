import { useContext, useEffect, useRef, useState } from "react";
import { useWebsocketMessage } from "../hooks/useWebsocketMessage";
import { WebsocketContext } from "../contexts/WebSocketContext";
import { isLocalStorageEmpty, resetClient } from "../helpers/utilities";
import type {
  ClientMessage,
  ClientReconnectMessage,
} from "../generated/message";
import {
  isServerFailedReconnectionMessage,
  isServerUUIDAssignmentMessage,
} from "../generated/message.guard";
import type { WebSocketInterface } from "../contexts/WebSocketProvider";

export function Handshake({
  completeHandshake,
  setErrorMessage,
}: {
  completeHandshake: () => void;
  setErrorMessage: (message: string) => void;
}) {
  const ws: WebSocketInterface = useContext(WebsocketContext);

  const [isReconnecting, setIsReconnecting] = useState(false);

  // Stop initial request being sent twice leading to the client being disconnected
  // Strict mode calls useEffect twice
  const hasSentRequestRef = useRef(false);

  useWebsocketMessage("uuid assignment", (message) => {
    if (isServerUUIDAssignmentMessage(message) && !isReconnecting) {
      localStorage["uuid"] = message.uuid;
      completeHandshake();
    }
  });

  useWebsocketMessage("successful reconnect", (_) => {
    completeHandshake();
  });

  useWebsocketMessage("failed reconnect", (message) => {
    if (isServerFailedReconnectionMessage(message)) {
      setErrorMessage(message.reason);
      if (message.shouldReset) {
        resetClient();
      }
    }
  });

  useEffect(() => {
    if (!hasSentRequestRef.current) {
      let msg;
      if (isLocalStorageEmpty("uuid")) {
        // If no uuid exists in localstorage, fresh connection
        setIsReconnecting(false);
        const handshakeMsg: ClientMessage = {
          type: "initial connect",
        };
        msg = handshakeMsg;
      } else {
        // If a uuid exists in memory, attempt to reconnect
        setIsReconnecting(true);
        const handshakeMsg: ClientReconnectMessage = {
          type: "reconnect",
          uuid: localStorage["uuid"],
        };
        msg = handshakeMsg;
      }
      ws.send(JSON.stringify(msg));
      hasSentRequestRef.current = true;
    }
  }, []);

  return <h1>🤝</h1>;
}
