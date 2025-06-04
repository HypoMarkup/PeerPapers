/*
 * Generated type guards for "message.d.ts".
 * WARNING: Do not manually change this file.
 */
import type {
  IncomingMessage,
  UUIDAssignmentMessage,
  FailedReconnectionMessage,
} from "./message";

export function isIncomingMessage(obj: unknown): obj is IncomingMessage {
  const typedObj = obj as IncomingMessage;
  return (
    ((typedObj !== null && typeof typedObj === "object") ||
      typeof typedObj === "function") &&
    (typedObj["type"] === "uuid-assignment" ||
      typedObj["type"] === "successful-reconnect" ||
      typedObj["type"] === "failed-reconnect")
  );
}

export function isUUIDAssignmentMessage(
  obj: unknown
): obj is UUIDAssignmentMessage {
  const typedObj = obj as UUIDAssignmentMessage;
  return (
    (isIncomingMessage(typedObj) as boolean) &&
    typedObj["type"] === "uuid-assignment" &&
    typeof typedObj["uuid"] === "string"
  );
}

export function isFailedReconnectionMessage(
  obj: unknown
): obj is FailedReconnectionMessage {
  const typedObj = obj as FailedReconnectionMessage;
  return (
    (isIncomingMessage(typedObj) as boolean) &&
    typedObj["type"] === "failed-reconnect" &&
    (typedObj["reason"] === "invalid-uuid" ||
      typedObj["reason"] === "server-full") &&
    typeof typedObj["shouldReset"] === "boolean"
  );
}
