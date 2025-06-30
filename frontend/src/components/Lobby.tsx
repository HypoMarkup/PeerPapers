import { useState } from "react";
import { useWebsocketMessage } from "../hooks/useWebsocketMessage";
import type { PlayerStatus } from "../generated/message";
import { isServerPlayersStatusBroadcast } from "../generated/message.guard";

export function Lobby({ name }: { name: string }) {
  const [playerStatus, setPlayerStatus] = useState<PlayerStatus[]>([]);

  useWebsocketMessage("players status", (message) => {
    if (isServerPlayersStatusBroadcast(message)) {
      setPlayerStatus(message.status);
      return true;
    }
    return false;
  });

  if (playerStatus.length === 0) {
    return <>Loading</>;
  }

  const list = playerStatus.map((player) => (
    <li key={player.name}>
      {player.isHost ? "👑" : "🔵"}{" "}
      <img
        width={20}
        height={20}
        src={player.pictureURL.length !== 0 ? player.pictureURL : undefined}
      ></img>
      {player.name == name ? (
        <strong>{player.name}</strong>
      ) : (
        <span>{player.name}</span>
      )}
    </li>
  ));

  return <ul>{list}</ul>;
}
