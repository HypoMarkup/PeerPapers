import { useContext, useEffect, useState } from "react";
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

  const [isReconnecting, setIsReconnecting] = useState(false);

  useEffect(() => {
    if (isLocalStorageEmpty("uuid")) {
      // If no uuid exists in localstorage, fresh connection
      setIsReconnecting(false);
      const handshakeMsg: ClientMessage = {
        type: "initial connect",
      };
      ws.send(JSON.stringify(handshakeMsg));
    } else {
      // If a uuid exists in memory, attempt to reconnect
      setIsReconnecting(true);
      const handshakeMsg: ClientReconnectMessage = {
        type: "reconnect",
        uuid: localStorage["uuid"],
      };
      ws.send(JSON.stringify(handshakeMsg));
    }
    const unregister = ws.registerHandler({
      messageTypes: new Set([
        "uuid assignment",
        "successful reconnect",
        "failed reconnect",
      ]),
      handler: (message) => {
        switch (message.type) {
          case "uuid assignment":
            if (isServerUUIDAssignmentMessage(message) && !isReconnecting) {
              localStorage["uuid"] = message.uuid;
              completeHandshake();
              return true;
            } else {
              return false;
            }
          case "successful reconnect":
            completeHandshake();
            return true;
          case "failed reconnect":
            if (isServerFailedReconnectionMessage(message)) {
              console.error(message);
              if (message.shouldReset) {
                resetClient();
              }
              return true;
            }
            return false;
          default:
            return false;
        }
      },
    });
    return unregister;
  }, []);

  return <h1>🤝</h1>;
}
