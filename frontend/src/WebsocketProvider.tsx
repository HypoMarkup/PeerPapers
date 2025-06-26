import { useState, useRef, useEffect, createContext } from "react";
import type { ReactNode } from "react";
import type { ServerMessage } from "./generated/message";
import { isServerMessage } from "./generated/message.guard";
import { Handshake } from "./Handshake";
import { resetClient } from "./utililties";

// Source:
// https://ably.com/blog/websockets-react-tutorial

export interface WebSocketInterface {
  message: ServerMessage;
  send: (data: string | ArrayBufferLike | Blob | ArrayBufferView) => void;
}

export const WebsocketContext = createContext<WebSocketInterface>({
  message: { type: "no operation" },
  send: () => {},
});

type iProps = { children?: ReactNode };

export const WebsocketProvider = (props: iProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isHandshakeComplete, setIsHandshakeComplete] = useState(false);

  const [message, setMessage] = useState<ServerMessage>({
    type: "no operation",
  });

  const ws = useRef<WebSocket>(null);

  useEffect(() => {
    // TODO: Store url in env variable or something that isn't a string literal
    // Dynamic url??? if we want to put clientID in the url
    const socket = new WebSocket("ws://127.0.0.1:8000/ws");

    socket.onopen = () => {
      if (ws.current?.readyState == 1) {
        setIsConnected(true);
      }
    };
    socket.onclose = () => {
      setIsConnected(false);
      resetClient();
    };
    socket.onmessage = (event) => {
      const m = JSON.parse(event.data);
      if (isServerMessage(m)) {
        setMessage(m);
      } else {
        console.error("Invalid message: " + event.data);
      }
    };

    ws.current = socket;

    return () => {
      if (isConnected) {
        socket.close();
      }
    };
  }, []);

  if (!isConnected || ws.current === null) {
    return <p>Connecting</p>;
  }

  const ret: WebSocketInterface = {
    message: message,
    send: ws.current.send.bind(ws.current),
  };

  if (!isHandshakeComplete) {
    return (
      <WebsocketContext.Provider value={ret}>
        <Handshake completeHandshake={() => setIsHandshakeComplete(true)} />
      </WebsocketContext.Provider>
    );
  }

  return (
    <WebsocketContext.Provider value={ret}>
      {props.children}
    </WebsocketContext.Provider>
  );
};
