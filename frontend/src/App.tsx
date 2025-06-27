import { useState } from "react";
import { ProfileEditor } from "./ProfileEditor";
import { Lobby } from "./Lobby";

function App() {
  const [name, setName] = useState("");
  const [pictureURL, setPictureURL] = useState("");

  return (
    <>
      <p>Connected</p>
      <ProfileEditor setName={setName} setPictureURL={setPictureURL} />
      {name.length !== 0 && <Lobby name={name} />}
    </>
  );
}

export default App;
