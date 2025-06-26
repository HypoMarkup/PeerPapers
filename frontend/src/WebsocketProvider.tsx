import { useState, useRef, useEffect, createContext, useContext } from "react";
import type { ReactNode } from "react";
import type { ServerMessage } from "./generated/message";
import { isServerMessage } from "./generated/message.guard";
import { Handshake } from "./Handshake";
import { resetClient } from "./utililties";

// Source:
// https://ably.com/blog/websockets-react-tutorial

export interface WebSocketInterface {
  registerHandler: (handler: MessageHandler) => () => void;
  send: (data: string | ArrayBufferLike | Blob | ArrayBufferView) => void;
}

export const WebsocketContext = createContext<WebSocketInterface>({
  registerHandler: (_) => () => {},
  send: () => {},
});

interface MessageHandler {
  messageType: ServerMessage["type"];
  handler: (message: ServerMessage) => boolean; // returns true if handled
}

type iProps = { children?: ReactNode };

export function useWebsocketMessage(
  messageType: ServerMessage["type"],
  handler: (message: ServerMessage) => boolean
) {
  const ws = useContext(WebsocketContext);

  useEffect(() => {
    return ws.registerHandler({
      messageType: messageType,
      handler: handler,
    });
  }, [handler]);
}

export const WebsocketProvider = (props: iProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isHandshakeComplete, setIsHandshakeComplete] = useState(false);

  const [message, setMessage] = useState<ServerMessage>();

  const handlersRef = useRef<MessageHandler[]>([]);

  const registerHandler = (handler: MessageHandler) => {
    handlersRef.current.push(handler);
    // Cleanup function
    return () => handlersRef.current.splice(handlersRef.current.length - 1, 1);
  };

  const processMessage = () => {
    if (message === undefined) return;

    let wasHandled = false;

    // Try each registered handler
    for (const handler of handlersRef.current) {
      if (handler.messageType === message.type) {
        wasHandled = handler.handler(message);
        if (wasHandled) break;
      }
    }

    if (!wasHandled) {
      console.warn(`No handler for message: ${message.type}`);
    }
  };

  useEffect(() => {
    processMessage();
  }, [message]);

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
    registerHandler: registerHandler,
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
