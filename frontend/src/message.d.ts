// Not quite sure how to handle this so we do interface inheritance 😼
// TODO: do some fancy stuff to break these down further and write instance checks

//
// Outgoing messages
//

export interface OutgoingMessage {
  type: "initial-connect" | "reconnect";
}

export interface ReconnectMessage extends OutgoingMessage {
  type: "reconnect";
  uuid: string;
}

//
// Ingoing messages
//

/** @see {isIncomingMessage} ts-auto-guard:type-guard */
export interface IncomingMessage {
  type: "uuid-assignment" | "successful-reconnect" | "failed-reconnect";
}

/** @see {isUUIDAssignmentMessage} ts-auto-guard:type-guard */
export interface UUIDAssignmentMessage extends IncomingMessage {
  type: "uuid-assignment";
  uuid: string;
}

/** @see {isFailedReconnectionMessage} ts-auto-guard:type-guard */
export interface FailedReconnectionMessage extends IncomingMessage {
  type: "failed-reconnect";
  reason: "invalid-uuid" | "server-full";
  shouldReset: boolean;
}
