import { useContext} from "react"
import { WebsocketContext, type WebSocketInterface } from "./WebsocketProvider"

function App() {
  // const [form, setForm] = useState("");

  const ws: WebSocketInterface = useContext(WebsocketContext);

  const isReady = ws.isReady ? "Ready" : "Not ready";
  const output = ws.value != null ? ws.value : "";

  return (
    <>
      <p>Status: {isReady}</p>
      <p>Data: {output}</p>
    </>
  )
}

export default App
