import { useState, useRef, useEffect, createContext, useContext } from "react";
import type { ReactNode } from "react";
import type { ServerMessage } from "./generated/message";
import { isServerMessage } from "./generated/message.guard";
import { Handshake } from "./Handshake";

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

type MessageHandlerFunction = (message: ServerMessage) => boolean;

interface MessageHandler {
  messageType: ServerMessage["type"];
  handler: MessageHandlerFunction; // returns true if handled
}

type iProps = { children?: ReactNode };

export function useWebsocketMessage(
  messageType: ServerMessage["type"],
  handler: MessageHandlerFunction
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

  const handlersRef = useRef<
    Map<ServerMessage["type"], MessageHandlerFunction[]>
  >(new Map());

  const registerHandler = (handler: MessageHandler) => {
    let arr = handlersRef.current.get(handler.messageType);
    if (arr !== undefined) {
      arr.push(handler.handler);
    } else {
      arr = [handler.handler];
      handlersRef.current.set(handler.messageType, arr);
    }
    // Cleanup function
    return () => arr.splice(arr.length - 1, 1);
  };

  const processMessage = () => {
    if (message === undefined) return;

    let wasHandled = false;

    const arr = handlersRef.current.get(message.type);
    if (arr !== undefined) {
      for (let i = 0; i < arr.length; i++) {
        wasHandled ||= arr[i](message);
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
      socket.close();
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
