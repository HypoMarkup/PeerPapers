import { useContext, useEffect, useRef } from "react";
import { WebsocketContext, type WebSocketInterface } from "./WebsocketProvider";
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

  const isReconnectingRef = useRef(false);

  // Stop initial request being sent twice leading to the client being disconnected
  // Strict mode calls useEffect twice
  const hasSentRequestRef = useRef(false);

  useEffect(() => {
    switch (ws.message.type) {
      case "uuid assignment":
        if (
          isServerUUIDAssignmentMessage(ws.message) &&
          !isReconnectingRef.current
        ) {
          localStorage["uuid"] = ws.message;
          completeHandshake();
        } else {
          console.error("Unexpected message: " + ws.message);
        }
        break;
      case "successful reconnect":
        if (isReconnectingRef.current) {
          completeHandshake();
        } else {
          console.error("Expected UUID assignment");
        }
        break;
      case "failed reconnect":
        if (
          isServerFailedReconnectionMessage(ws.message) &&
          isReconnectingRef.current
        ) {
          console.error(ws.message);
          if (ws.message.shouldReset) {
            resetClient();
          }
        }
        break;
      default:
        console.error("Expected UUID handshake");
    }
  }, [ws.message]);

  useEffect(() => {
    if (!hasSentRequestRef.current) {
      let msg;
      if (isLocalStorageEmpty("uuid")) {
        // If no uuid exists in localstorage, fresh connection
        isReconnectingRef.current = false;
        const handshakeMsg: ClientMessage = {
          type: "initial connect",
        };
        msg = handshakeMsg;
      } else {
        // If a uuid exists in memory, attempt to reconnect
        isReconnectingRef.current = true;
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
