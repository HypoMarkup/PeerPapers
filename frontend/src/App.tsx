import { useContext, useEffect, useState } from "react";
import { ProfileEditor } from "./ProfileEditor";
import { WebsocketContext } from "./WebsocketProvider";

function App() {
  const [name, setName] = useState("");
  const [pictureURL, setPictureURL] = useState("");

  return (
    <>
      <p>Connected</p>
      <ProfileEditor setName={setName} setPictureURL={setPictureURL} />
    </>
  );
}

export default App;
