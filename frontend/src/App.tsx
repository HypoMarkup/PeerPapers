import { useContext, useState } from "react";
import { WebsocketContext, type WebSocketInterface } from "./WebsocketProvider";

function App() {
  // const [form, setForm] = useState<string>("");
  // const [data, setData] = useState<string[]>([]);

  // const ws: WebSocketInterface = useContext(WebsocketContext);

  // const isReady = ws.isReady ? "Ready" : "Not ready";
  // const output = ws.message != null ? ws.message : "";

  // if (
  //   (ws.message != data[data.length - 1] || data.length == 0) &&
  //   ws.message != null
  // ) {
  //   setData([...data, ws.message]);
  // }

  // const chat = data.map((val: string, index: number) => (
  //   <p key={index}>{val}</p>
  // ));

  return (
    <p>Hi</p>
    // <>
    //   <input type="text" onChange={(e) => setForm(e.target.value)} />
    //   <button
    //     onClick={() => {
    //       if (ws.send != undefined) {
    //         ws.send(form);
    //         setForm("");
    //       }
    //     }}
    //   >
    //     Submit
    //   </button>
    //   <p>Status: {isReady}</p>
    //   <p>Data: {output}</p>
    //   {chat}
    // </>
  );
}

export default App;
