import { useState, useRef, useEffect, createContext } from "react";
import type { ReactNode } from "react";
import type {
  IncomingMessage,
  OutgoingMessage,
  ReconnectMessage,
} from "./message";
import { isUUIDAssignmentMessage, isIncomingMessage } from "./message.guard";

// Source:
// https://ably.com/blog/websockets-react-tutorial

function isLocalStorageEmpty(key: string): boolean {
  return localStorage[key] === undefined || localStorage[key].length === 0;
}

function resetClient() {
  localStorage.clear();
  location.reload();
}

export interface WebSocketInterface {
  isReady: boolean;
  UUID: string | null;
  message: IncomingMessage | null;
  send:
    | ((data: string | ArrayBufferLike | Blob | ArrayBufferView) => void)
    | undefined;
}

export const WebsocketContext = createContext<WebSocketInterface>({
  isReady: false,
  message: null,
  UUID: null,
  send: () => {},
});

type iProps = { children?: ReactNode };

export const WebsocketProvider = (props: iProps) => {
  // Ready
  const [isReady, setIsReady] = useState(false);

  const [msg, setMsg] = useState<IncomingMessage | null>(null);

  // TODO: Add checks on entered name to prevent empty names and other
  const [uuid, setUUID] = useState<string>("");

  const ws = useRef<WebSocket>(null);

  useEffect(() => {
    // TODO: Store url in env variable or something that isn't a string literal
    // Dynamic url??? if we want to put clientID in the url
    const socket = new WebSocket("ws://127.0.0.1:8000/ws");

    socket.onopen = () => {
      if (isLocalStorageEmpty("uuid")) {
        // If no uuid exists in localstorage, fresh connection
        const handshakeMsg: OutgoingMessage = {
          type: "initial-connect",
        };
        ws.current?.send(JSON.stringify(handshakeMsg));
      } else if (!isLocalStorageEmpty("uuid")) {
        // If a uuid exists in memory, attempt to reconnect
        const handshakeMsg: ReconnectMessage = {
          type: "reconnect",
          uuid: localStorage["uuid"],
        };
        ws.current?.send(JSON.stringify(handshakeMsg));
      } else {
        resetClient();
      }
    };
    socket.onclose = () => setIsReady(false);
    socket.onmessage = (event) => {
      const m = JSON.parse(event.data);
      if (isIncomingMessage(m)) {
        setMsg(m);
      } else {
        console.error("Invalid message: " + event.data);
      }
    };

    ws.current = socket;
    ws.current.send;

    return () => {
      socket.close();
    };
  }, []);

  if (!isReady && msg !== null) {
    if (isUUIDAssignmentMessage(msg)) {
      setUUID(msg.uuid);
      setIsReady(true);
      localStorage["uuid"] = msg.uuid;
    } else if (isIncomingMessage(msg)) {
      if (msg.type == "successful-reconnect") {
        setUUID(localStorage["uuid"]);
        setIsReady(true);
      } else if (msg.type == "failed-reconnect") {
        resetClient();
      }
    } else {
      console.error("Expected UUID handshake");
    }
  }

  const ret: WebSocketInterface = {
    isReady: isReady,
    UUID: uuid,
    message: msg,
    send: ws.current?.send.bind(ws.current),
  };

  return (
    <WebsocketContext.Provider value={ret}>
      {props.children}
    </WebsocketContext.Provider>
  );
};
