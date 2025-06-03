/*
 * Generated type guards for "message.d.ts".
 * WARNING: Do not manually change this file.
 */
import type { IncomingMessage, AssignUUIDMessage } from "./message";

export function isIncomingMessage(obj: unknown): obj is IncomingMessage {
  const typedObj = obj as IncomingMessage;
  return (
    ((typedObj !== null && typeof typedObj === "object") ||
      typeof typedObj === "function") &&
    (typedObj["type"] === "assignUUID" ||
      typedObj["type"] === "validUUID" ||
      typedObj["type"] === "invalidUUID")
  );
}

export function isAssignUUIDMessage(obj: unknown): obj is AssignUUIDMessage {
  const typedObj = obj as AssignUUIDMessage;
  return (
    (isIncomingMessage(typedObj) as boolean) &&
    typedObj["type"] === "assignUUID" &&
    typeof typedObj["uuid"] === "string"
  );
}
