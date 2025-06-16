import { useContext, useState } from "react";
import { WebsocketContext, type WebSocketInterface } from "./WebsocketProvider";
import type { ClientSetPlayerDataMessage } from "./generated/message";

function PlayerDataEntry({
  submit,
}: {
  submit: (name: string, picture: string) => void;
}) {
  const [name, setName] = useState("");
  const [picture, setPicture] = useState("");

  return (
    <>
      <form>
        <label>Name: </label>
        <input type="text" onChange={(e) => setName(e.target.value)}></input>
      </form>

      <form>
        <label>Picture: </label>
        <input type="text" onChange={(e) => setPicture(e.target.value)}></input>
      </form>

      <img
        src={picture.length != 0 ? picture : undefined}
        width={100}
        height={100}
      />
      <button onClick={() => submit(name, picture)}>Submit</button>
    </>
  );
}

function App() {
  const ws: WebSocketInterface = useContext(WebsocketContext);
  if (!ws.isReady) {
    return <p>Not connected</p>;
  }

  return (
    <>
      <p>Connected</p>
      <p>{ws.message != null ? JSON.stringify(ws.message) : ""}</p>
      <PlayerDataEntry
        submit={(name, picture) => {
          const msg: ClientSetPlayerDataMessage = {
            type: "set player data",
            name: name,
            picture: picture,
          };
          if (ws.isReady && ws.send != undefined) {
            ws.send(JSON.stringify(msg));
          }
        }}
      />
    </>
  );
}

export default App;
