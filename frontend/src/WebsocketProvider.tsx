import { useState, useRef, useEffect, createContext} from "react"
import type { ReactNode } from "react";

// Source:
// https://ably.com/blog/websockets-react-tutorial

export interface WebSocketInterface{
  isReady: boolean;
  value: string | null;
  send: ((data: string | ArrayBufferLike | Blob | ArrayBufferView) => void) | undefined;
}

export const WebsocketContext = createContext<WebSocketInterface>({
  isReady: false,
  value: null,
  send: () => {}
})

type iProps = {children? : ReactNode}

export const WebsocketProvider = (props: iProps) => {
  const [isReady, setIsReady] = useState(false)
  const [val, setVal] = useState(null)

  const ws = useRef<WebSocket>(null)

  useEffect(() => {
    // TODO: Store url in env variable or something that isn't a string literal
    // Dyanmic url??? if we want to put clientID in the url
    const socket = new WebSocket("ws://127.0.0.1:8000/ws")

    socket.onopen = () => setIsReady(true)
    socket.onclose = () => setIsReady(false)
    socket.onmessage = (event) => setVal(event.data)

    ws.current = socket
    ws.current.send

    return () => {
      socket.close()
    }
  }, [])

  const ret: WebSocketInterface = {isReady: isReady, value: val, send: ws.current?.send.bind(ws.current)};

  return (
    <WebsocketContext.Provider value={ret}>
      {props.children}
    </WebsocketContext.Provider>
  )
}
