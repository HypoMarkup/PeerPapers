import { useContext, useEffect } from "react";
import type { ServerMessage } from "../generated/message";
import { WebsocketContext } from "../contexts/WebSocketContext";
import type { MessageHandlerFunction } from "../contexts/WebSocketProvider";

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
