import { useContext } from "react"
import { WebsocketContext, type WebSocketInterface } from "./WebsocketProvider"

function App() {
  const wsData: WebSocketInterface = useContext(WebsocketContext);

  const output = wsData.isReady ? "Ready"  : "Not ready";

  return (
    <>
      {output}
    </>
  )
}

export default App
