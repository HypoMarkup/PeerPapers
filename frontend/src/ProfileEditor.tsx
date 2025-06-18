// Attempt to fetch
// Display editor + Preview
// Autofill previous data if possible
// Allow new details to be input
// Have a live preview
// Allow them to be submit
// Show errors if needed

// TODO: message for data updated successfully

import { useContext, useEffect, useState } from "react";
import type { ClientMessage } from "./generated/message";
import { WebsocketContext, type WebSocketInterface } from "./WebsocketProvider";
import { isServerSendPlayerDataMessage } from "./generated/message.guard";

export function ProfileEditor({
  setName,
  setPictureURL,
}: {
  setName: (name: string) => void;
  setPictureURL: (pictureURL: string) => void;
}) {
  const ws: WebSocketInterface = useContext(WebsocketContext);

  const [initialRequestComplete, setInitialRequestComplete] = useState(false);

  const [nameForm, setNameForm] = useState("");
  const [pictureURLForm, setPictureURLForm] = useState("");

  useEffect(() => {
    const msg: ClientMessage = {
      type: "get player data",
    };
    if (ws.isReady && ws.send != undefined) ws.send(JSON.stringify(msg));
  }, []);

  if (
    ws.message?.type == "send player data" &&
    isServerSendPlayerDataMessage(ws.message) &&
    !initialRequestComplete
  ) {
    const msg = ws.message;

    setNameForm(msg.name);
    setPictureURLForm(msg.pictureURL);

    if (msg.name.length > 0 && msg.pictureURL.length > 0) {
      setName(msg.name);
      setPictureURL(msg.pictureURL);
    }
    setInitialRequestComplete(true);
  }

  if (!initialRequestComplete) {
    return <p>Loading</p>;
  }

  return (
    <>
      <h1>Hello</h1>
    </>
  );
}
