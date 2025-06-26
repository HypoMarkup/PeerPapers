import { useState } from "react";
import { ProfileEditor } from "./ProfileEditor";

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
