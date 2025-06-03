// Not quite sure how to handle this so we do interface inheritance 😼
// TODO: do some fancy stuff to break these down further and write instance checks

//
// Outgoing messages
//

export interface OutgoingMessage {
  type: "acquireUUID" | "checkUUID";
}

export interface CheckUUIDMessage extends OutgoingMessage {
  type: "checkUUID";
  uuid: string;
}

//
// Ingoing messages
//

/** @see {isIncomingMessage} ts-auto-guard:type-guard */
export interface IncomingMessage {
  type: "assignUUID" | "validUUID" | "invalidUUID";
}

/** @see {isAssignUUIDMessage} ts-auto-guard:type-guard */
export interface AssignUUIDMessage extends IncomingMessage {
  type: "assignUUID";
  uuid: string;
}
