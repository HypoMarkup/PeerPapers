/*
 * Generated type guards for "message.d.ts".
 * WARNING: Do not manually change this file.
 */
import { OutgoingMessage, ReconnectMessage, IncomingMessage, UUIDAssignmentMessage, FailedReconnectionMessage } from "./message";

export function isOutgoingMessage(obj: unknown): obj is OutgoingMessage {
    const typedObj = obj as OutgoingMessage
    return (
        (typedObj !== null &&
            typeof typedObj === "object" ||
            typeof typedObj === "function") &&
        (typedObj["type"] === "initial-connect" ||
            typedObj["type"] === "reconnect")
    )
}

export function isReconnectMessage(obj: unknown): obj is ReconnectMessage {
    const typedObj = obj as ReconnectMessage
    return (
        isOutgoingMessage(typedObj) as boolean &&
        typedObj["type"] === "reconnect" &&
        typeof typedObj["uuid"] === "string"
    )
}

export function isIncomingMessage(obj: unknown): obj is IncomingMessage {
    const typedObj = obj as IncomingMessage
    return (
        (typedObj !== null &&
            typeof typedObj === "object" ||
            typeof typedObj === "function") &&
        (typedObj["type"] === "uuid-assignment" ||
            typedObj["type"] === "successful-reconnect" ||
            typedObj["type"] === "failed-reconnect")
    )
}

export function isUUIDAssignmentMessage(obj: unknown): obj is UUIDAssignmentMessage {
    const typedObj = obj as UUIDAssignmentMessage
    return (
        isIncomingMessage(typedObj) as boolean &&
        typedObj["type"] === "uuid-assignment" &&
        typeof typedObj["uuid"] === "string"
    )
}

export function isFailedReconnectionMessage(obj: unknown): obj is FailedReconnectionMessage {
    const typedObj = obj as FailedReconnectionMessage
    return (
        isIncomingMessage(typedObj) as boolean &&
        typedObj["type"] === "failed-reconnect" &&
        (typedObj["reason"] === "invalid-uuid" ||
            typedObj["reason"] === "server-full") &&
        typeof typedObj["shouldReset"] === "boolean"
    )
}
