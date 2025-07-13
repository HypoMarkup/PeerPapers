import { useCallback, useState } from "react";
import { ProfileEditor } from "./components/ProfileEditor";
import { Lobby } from "./components/Lobby";
import { useWebsocketMessage } from "./hooks/useWebsocketMessage";
import {
  isServerPlayersStatusBroadcast,
  isServerStateBroadcast,
} from "./generated/message.guard";
import { HostLobby } from "./components/HostLobby";
import type { ServerState } from "./generated/message";

function App() {
  const [name, setName] = useState("");
  const [pictureURL, setPictureURL] = useState("");
  const [isHost, setIsHost] = useState(false);
  const [state, setState] = useState<ServerState>("LOBBY_NOT_READY");

  useWebsocketMessage(
    "players status",
    useCallback(
      (message) => {
        if (isServerPlayersStatusBroadcast(message)) {
          const player = message.status.filter((p) => p.name == name);
          if (player.length === 1) {
            setIsHost(player[0].isHost);
          } else {
            // Either player has not joined yet or two players
            // have the same name which should be impossible
            console.assert(player.length === 0);
          }
        }
      },
      [setIsHost, name]
    )
  );

  useWebsocketMessage(
    "state",
    useCallback((message) => {
      if (isServerStateBroadcast(message)) {
        setState(message.state);
      }
    }, [])
  );

  if (state === "LOBBY_NOT_READY" || state === "LOBBY_READY") {
    return (
      <>
        <p>Connected | {state === "LOBBY_READY" ? "Ready" : "Not ready"}</p>
        <ProfileEditor setName={setName} setPictureURL={setPictureURL} />
        {name.length !== 0 && <Lobby name={name} />}
        {isHost && <HostLobby isReady={state === "LOBBY_READY"} />}
      </>
    );
  } else {
    return <p>We made it to the moon</p>;
  }
}

export default App;
