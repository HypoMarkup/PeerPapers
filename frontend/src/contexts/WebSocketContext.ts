import { createContext } from "react";
import type { WebSocketInterface } from "./WebSocketProvider";

// Source:
// https://ably.com/blog/websockets-react-tutorial

export const WebsocketContext = createContext<WebSocketInterface>({
  registerHandler: (_) => () => {},
  send: () => {},
});
