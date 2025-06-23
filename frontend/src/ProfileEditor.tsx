// Attempt to fetch
// Display editor + Preview
// Autofill previous data if possible
// Allow new details to be input
// Have a live preview
// Allow them to be submit
// Show errors if needed

// TODO: message for data updated successfully

import { useContext, useEffect, useState } from "react";
import type {
  ClientMessage,
  ClientSetPlayerDataMessage,
} from "./generated/message";
import { WebsocketContext, type WebSocketInterface } from "./WebsocketProvider";
import {
  isServerActionFailMessage,
  isServerActionSuccessMessage,
  isServerSendPlayerDataMessage,
} from "./generated/message.guard";

// Enums bad or something "Enums are non erasable TypeScript code"
type RequestState =
  | "uninitialised"
  | "idle"
  | "awaitingGetResult"
  | "awaitingSetResult";

type ResultFlag = "none" | "success" | "failure";

export function ProfileEditor({
  setName,
  setPictureURL,
}: {
  setName: (name: string) => void;
  setPictureURL: (pictureURL: string) => void;
}) {
  const ws: WebSocketInterface = useContext(WebsocketContext);

  const [requestState, setRequestState] =
    useState<RequestState>("uninitialised");
  const [resultFlag, setResultFlag] = useState<ResultFlag>("none");
  const [errorMessage, setErrorMessage] = useState("");

  const [nameForm, setNameForm] = useState("");
  const [pictureURLForm, setPictureURLForm] = useState("");

  useEffect(() => {
    const msg: ClientMessage = {
      type: "get player data",
    };
    if (ws.isReady && ws.send != undefined) {
      ws.send(JSON.stringify(msg));
      setRequestState("awaitingGetResult");
    }
  }, []);

  useEffect(() => {
    if (
      requestState == "awaitingGetResult" &&
      ws.message?.type == "send player data" &&
      isServerSendPlayerDataMessage(ws.message)
    ) {
      const msg = ws.message;
      setNameForm(msg.name);
      setPictureURLForm(msg.pictureURL);

      if (msg.name.length > 0 && msg.pictureURL.length > 0) {
        setName(msg.name);
        setPictureURL(msg.pictureURL);
      }
      setRequestState("idle");
    }

    if (requestState == "awaitingSetResult") {
      if (
        ws.message?.type == "action success" &&
        isServerActionSuccessMessage(ws.message) &&
        ws.message.actionType == "set player data"
      ) {
        // Set flag for like successfully set
        setName(nameForm);
        setPictureURL(pictureURLForm);
        setResultFlag("success");
        setRequestState("idle");
      } else if (
        ws.message?.type == "action fail" &&
        isServerActionFailMessage(ws.message) &&
        ws.message.actionType == "set player data"
      ) {
        setResultFlag("failure");
        setRequestState("idle");
        setErrorMessage(ws.message.reason);
      }
    }
  }, [ws.message]);

  if (requestState != "idle") {
    return <p>Loading</p>;
  }

  return (
    <>
      <form>
        <label>Name: </label>
        <input
          type="text"
          value={nameForm}
          onChange={(e) => setNameForm(e.target.value)}
        ></input>
      </form>
      <form>
        <label>Picture URL: </label>
        <input
          type="text"
          value={pictureURLForm}
          onChange={(e) => setPictureURLForm(e.target.value)}
        ></input>
      </form>
      <button
        onClick={() => {
          const msg: ClientSetPlayerDataMessage = {
            type: "set player data",
            name: nameForm,
            pictureURL: pictureURLForm,
          };
          if (ws.isReady && ws.send != undefined) {
            ws.send(JSON.stringify(msg));
            setRequestState("awaitingSetResult");
          }
        }}
      >
        Submit
      </button>
      {resultFlag == "success" && <p>Successfully set</p>}
      {resultFlag == "failure" && <p>{errorMessage}</p>}
      <h2>Preview</h2>
      <img
        src={pictureURLForm.length != 0 ? pictureURLForm : undefined}
        width={200}
        height={200}
      ></img>
      <p>{nameForm}</p>
    </>
  );
}
