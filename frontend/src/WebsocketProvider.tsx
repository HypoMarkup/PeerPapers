import { useState, useRef, useEffect, createContext } from "react";
import type { ReactNode } from "react";
import type { IncomingMessage, OutgoingMessage } from "./message";
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
  const [isReady, setIsReady] = useState(false);
  const [rawData, setRawData] = useState<String>();

  const [msg, setMsg] = useState<IncomingMessage | null>(null);
  const [uuid, setUUID] = useState<string>("");
  const [handshakeComplete, setHandshakeComplete] = useState(false);

  const ws = useRef<WebSocket>(null);

  useEffect(() => {
    // TODO: Store url in env variable or something that isn't a string literal
    // Dynamic url??? if we want to put clientID in the url
    const socket = new WebSocket("ws://127.0.0.1:8000/ws");

    socket.onopen = () => {
      if (!handshakeComplete) {
        const msg: OutgoingMessage = {
          type: "acquireUUID",
        };
        ws.current?.send(JSON.stringify(msg));
      }
      setIsReady(true);
    };
    socket.onclose = () => setIsReady(false);
    socket.onmessage = (event) => {
      setRawData(event.data);

      // Add validation at some point (instance of IngoingMessage check)
      const m = JSON.parse(event.data);
      if (isIncomingMessage(m)) {
        setMsg(m);
      }
    };

    ws.current = socket;
    ws.current.send;

    return () => {
      socket.close();
    };
  }, []);

  useEffect(() => {
    if (handshakeComplete) {
      setIsReady(true);
    }
  }, [handshakeComplete]);

  console.log(msg);

  if (!handshakeComplete && isReady && msg !== null) {
    if (isAssignUUIDMessage(msg)) {
      setUUID(msg.uuid);
      setHandshakeComplete(true);
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
