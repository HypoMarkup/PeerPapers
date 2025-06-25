import { useContext, useEffect, useRef, useState } from "react";
import {
  useWebsocketMessage,
  WebsocketContext,
  type WebSocketInterface,
} from "./WebsocketProvider";
import { isLocalStorageEmpty, resetClient } from "./utililties";
import type {
  ClientMessage,
  ClientReconnectMessage,
} from "./generated/message";
import {
  isServerFailedReconnectionMessage,
  isServerUUIDAssignmentMessage,
} from "./generated/message.guard";

export function Handshake({
  completeHandshake,
}: {
  completeHandshake: () => void;
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
      return true;
    } else {
      return false;
    }
  });

  useWebsocketMessage("successful reconnect", (_) => {
    completeHandshake();
    return true;
  });

  useWebsocketMessage("failed reconnect", (message) => {
    if (isServerFailedReconnectionMessage(message)) {
      console.error(message);
      if (message.shouldReset) {
        resetClient();
      }
      return true;
    }
    return false;
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
