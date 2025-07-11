import { useCallback, useState } from "react";
import { ProfileEditor } from "./components/ProfileEditor";
import { Lobby } from "./components/Lobby";
import { useWebsocketMessage } from "./hooks/useWebsocketMessage";
import {
  isServerPlayersStatusBroadcast,
  isServerSendPlayerDataMessage,
} from "./generated/message.guard";

function App() {
  const [name, setName] = useState("");
  const [pictureURL, setPictureURL] = useState("");
  const [isHost, setIsHost] = useState(false);

  useWebsocketMessage(
    "players status",
    useCallback(
      (message) => {
        if (isServerPlayersStatusBroadcast(message)) {
          const player = message.status.filter((p) => p.name == name);
          console.log(player);
          if (player.length === 1) {
            setIsHost(player[0].isHost);
          } else {
            // Either player has not joined yet or two players
            // have the same name which should be impossible
            console.assert(player.length === 0);
          }
          return true;
        }
        return false;
      },
      [setIsHost, name]
    )
  );

  return (
    <>
      <p>Connected</p>
      <ProfileEditor setName={setName} setPictureURL={setPictureURL} />
      {name.length !== 0 && <Lobby name={name} />}
      {isHost && <p>Yay you're the host, this is amazing</p>}
    </>
  );
}

export default App;
