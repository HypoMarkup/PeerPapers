import { useContext, useState } from "react";
import { WebsocketContext, type WebSocketInterface } from "./WebsocketProvider";
import { ProfileEditor } from "./ProfileEditor";

function App() {
  // const ws: WebSocketInterface = useContext(WebsocketContext);

  // const [name, setName] = useState("");
  // const [pictureURL, setPictureURL] = useState("");

  // if (!ws.isReady) {
  //   return <p>Not connected</p>;
  // }

  // return (
  //   <>
  //     <p>Connected</p>
  //     <p>{ws.message != null ? JSON.stringify(ws.message) : ""}</p>
  //     <ProfileEditor setName={setName} setPictureURL={setPictureURL} />
  //   </>
  // );
  return <h1>Hi</h1>;
}

export default App;
