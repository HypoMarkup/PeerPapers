# Websockets

## Frontend

### How to use a websocket message in my component?

Use the `useWebsocketMessage` hook!

#### Api

```tsx
useWebsocketMessage(messageType, handler);
```

- messageType: String indicating which message type you want to handle
- handler: function which takes a `ServerMessage` object as a parameter and returns `true` or `false` depending on whether or not the message was handled

#### Example component

```tsx
function Example() {
  const [uuid, setUuid] = useState<String>("");

  useWebsocketMessage(
    "uuid assignment",
    useCallback(
      (message) => {
        if (isServerUUIDAssignmentMessage(message)) {
          if (uuid == "") {
            setUuid(message.uuid);
          } else {
            console.error("UUID is already set");
          }
        }
      },
      [uuid]
    )
  );

  return <p>My uuid: {uuid}</p>;
}
```

This component waits for a `uuid assignment` message. If it's uuid has not been set yet, it sets it to the uuid in the message, otherwise it throws an error.

> [!IMPORTANT]
> Notice how we wrapped the handler function in a useCallback and placed all the stateful variables (just `uuid`) we used in the dependency array. **This is not necessary but highly recommended**. useCallback memoizes (caches) the function instead of generating a new function on each render. It only generates a new function when the value of one of the stateful variables in the dependency array changes. If you omit stateful variables which you used, a stale (old value) of the variable will be used which can lead to bugs

### How to send websocket messages from my component

```tsx
const ws: WebSocketInterface = useContext(WebsocketContext);
ws.send("my data");
```

#### Example component

```tsx
function Example() {
  const ws: WebSocketInterface = useContext(WebsocketContext);
  return <button onClick={() => ws.send("Hi")}>Click me</button>;
}
```
