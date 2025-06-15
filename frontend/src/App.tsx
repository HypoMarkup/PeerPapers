import { useContext } from "react";
import { WebsocketContext, type WebSocketInterface } from "./WebsocketProvider";

function App() {
  const ws: WebSocketInterface = useContext(WebsocketContext);
  return <p>{ws.isReady ? "Connected" : "Not connected"}</p>;
}

export default App;
