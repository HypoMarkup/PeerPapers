import { useState, useRef, useEffect, createContext } from "react";
import type { ReactNode } from "react";
import type {
  IncomingMessage,
  OutgoingMessage,
  CheckUUIDMessage,
} from "./message";
import { isAssignUUIDMessage, isIncomingMessage } from "./message.guard";

// Source:
// https://ably.com/blog/websockets-react-tutorial

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
  const [uuid, setUUID] = useState<string>("");

  const ws = useRef<WebSocket>(null);

  useEffect(() => {
    // TODO: Store url in env variable or something that isn't a string literal
    // Dynamic url??? if we want to put clientID in the url
    const socket = new WebSocket("ws://127.0.0.1:8000/ws");

    socket.onopen = () => {
      if (
        localStorage["uuid"] === undefined ||
        localStorage["uuid"].length === 0
      ) {
        // If no uuid exists in localstorage, request a uuid
        const handshakeMsg: OutgoingMessage = {
          type: "acquireUUID",
        };
        ws.current?.send(JSON.stringify(handshakeMsg));
      } else {
        // If a uuid exists in memory, check it
        const handshakeMsg: CheckUUIDMessage = {
          type: "checkUUID",
          uuid: localStorage["uuid"],
        };
        ws.current?.send(JSON.stringify(handshakeMsg));
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
    if (isAssignUUIDMessage(msg)) {
      setUUID(msg.uuid);
      setIsReady(true);
      localStorage["uuid"] = msg.uuid;
    } else if (isIncomingMessage(msg)) {
      if (msg.type == "validUUID") {
        setUUID(localStorage["uuid"]);
        setIsReady(true);
      } else if (msg.type == "invalidUUID") {
        localStorage.clear();
        location.reload();
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
