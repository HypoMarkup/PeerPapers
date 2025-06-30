// Attempt to fetch
// Display editor + Preview
// Autofill previous data if possible
// Allow new details to be input
// Have a live preview
// Allow them to be submit
// Show errors if needed

// TODO: message for data updated successfully

import { useCallback, useContext, useEffect, useState } from "react";
import type {
  ClientMessage,
  ClientSetPlayerDataMessage,
} from "../generated/message";
import { useWebsocketMessage } from "../hooks/useWebsocketMessage";
import { WebsocketContext } from "../contexts/WebSocketContext";
import {
  isServerActionFailMessage,
  isServerActionSuccessMessage,
  isServerSendPlayerDataMessage,
} from "../generated/message.guard";
import type { WebSocketInterface } from "../contexts/WebsocketProvider";

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

  useWebsocketMessage(
    "send player data",
    useCallback(
      (message) => {
        if (
          requestState == "awaitingGetResult" &&
          isServerSendPlayerDataMessage(message)
        ) {
          setNameForm(message.name);
          setPictureURLForm(message.pictureURL);

          if (message.name.length > 0 && message.pictureURL.length > 0) {
            setName(message.name);
            setPictureURL(message.pictureURL);
          }
          setRequestState("idle");
          return true;
        } else {
          return false;
        }
      },
      [requestState, setName, setPictureURL]
    )
  );

  useWebsocketMessage(
    "action success",
    useCallback(
      (message) => {
        if (
          isServerActionSuccessMessage(message) &&
          requestState === "awaitingSetResult" &&
          message.actionType === "set player data"
        ) {
          setName(nameForm);
          setPictureURL(pictureURLForm);
          setResultFlag("success");
          setRequestState("idle");
          return true;
        } else {
          return false;
        }
      },
      [nameForm, pictureURLForm, requestState, setName, setPictureURL]
    )
  );

  useWebsocketMessage(
    "action fail",
    useCallback(
      (message) => {
        if (
          isServerActionFailMessage(message) &&
          requestState === "awaitingSetResult" &&
          message.actionType == "set player data"
        ) {
          setResultFlag("failure");
          setRequestState("idle");
          setErrorMessage(message.reason);
          return true;
        } else {
          return false;
        }
      },
      [requestState]
    )
  );

  useEffect(() => {
    if (requestState == "uninitialised") {
      const msg: ClientMessage = {
        type: "get player data",
      };
      ws.send(JSON.stringify(msg));
      setRequestState("awaitingGetResult");
    }
  }, []);

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
          onChange={(e) => setNameForm(e.target.value.toLowerCase())}
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
          ws.send(JSON.stringify(msg));
          setRequestState("awaitingSetResult");
        }}
      >
        Submit
      </button>
      {resultFlag == "success" && <p>Successfully set</p>}
      {resultFlag == "failure" && <p>{errorMessage}</p>}
      <h2>Preview</h2>
      <img
        src={pictureURLForm.length !== 0 ? pictureURLForm : undefined}
        width={200}
        height={200}
      ></img>
      <p>{nameForm}</p>
    </>
  );
}
