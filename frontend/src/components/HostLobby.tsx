// https://uploadcare.com/blog/how-to-upload-file-in-react/
import React, { useCallback, useContext, useState } from "react";
import { getBase64 } from "../helpers/utilities";
import type { WebSocketInterface } from "../contexts/WebsocketProvider";
import { WebsocketContext } from "../contexts/WebSocketContext";
import type { ClientHostSetPDF } from "../generated/message";
import { useWebsocketMessage } from "../hooks/useWebsocketMessage";
import {
  isServerActionFailMessage,
  isServerActionSuccessMessage,
} from "../generated/message.guard";

export function HostLobby() {
  const [file, setFile] = useState<File | null>(null);
  const ws: WebSocketInterface = useContext(WebsocketContext);
  const [statusMessage, setStatusMessage] = useState("");

  useWebsocketMessage(
    "action success",
    useCallback(
      (message) => {
        if (isServerActionSuccessMessage(message)) {
          if (message.actionType == "host set pdf") {
            setStatusMessage("Successfully set PDF");
          }
        }
      },
      [setStatusMessage]
    )
  );

  useWebsocketMessage(
    "action fail",
    useCallback(
      (message) => {
        if (isServerActionFailMessage(message)) {
          if (message.actionType == "host set pdf") {
            setStatusMessage(message.reason);
          }
        }
      },
      [setStatusMessage]
    )
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (file) {
      getBase64(file).then((base64PDF) => {
        const message: ClientHostSetPDF = {
          type: "host set pdf",
          base64PDF: base64PDF as string,
        };
        ws.send(JSON.stringify(message));
      });
    }
  };

  return (
    <>
      {statusMessage.length !== 0 && <p>{statusMessage}</p>}
      <input id="file" type="file" accept=".pdf" onChange={handleFileChange} />
      {file && (
        <section>
          File details:
          <ul>
            <li>Name: {file.name}</li>
            <li>Type: {file.type}</li>
            <li>Size: {file.size} bytes</li>
          </ul>
        </section>
      )}

      {file && (
        <button onClick={handleUpload} className="submit">
          Upload a file
        </button>
      )}
    </>
  );
}
