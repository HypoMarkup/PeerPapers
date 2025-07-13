from pydantic import BaseModel
from typing import Literal, List

from enum import Enum


class ServerState(Enum):
    LOBBY_NOT_READY = "LOBBY_NOT_READY"
    LOBBY_READY = "LOBBY_READY"


#
# Client messages
#

# Types which have a generic fail and success message
actionTypes = Literal["set player data", "host set pdf"]

ClientMessageTypes = Literal[
    "initial connect", "reconnect", "set player data", "get player data", "host set pdf"
]


class ClientMessage(BaseModel):
    type: ClientMessageTypes


class ClientConnectMessage(BaseModel):
    type: Literal["initial connect"]


class ClientReconnectMessage(BaseModel):
    type: Literal["reconnect"]
    uuid: str


class ClientSetPlayerDataMessage(BaseModel):
    type: Literal["set player data"]

    name: str
    pictureURL: str


class ClientHostSetPDF(BaseModel):
    type: Literal["host set pdf"]
    base64PDF: str


#
# Server messages
#

ServerMessageTypes = Literal[
    # Handshake start
    "uuid assignment",
    "successful reconnect",
    "failed reconnect",
    # Handshake end
    "action success",
    "action fail",
    "send player data",
    "players status",
    "pdf",
]


class ServerMessage(BaseModel):
    type: ServerMessageTypes


# Message to be used in cases where a client message can or success fail
# e.g. when setting player data
class ServerActionSuccessMessage(BaseModel):
    type: Literal["action success"]
    actionType: actionTypes


class ServerActionFailMessage(BaseModel):
    type: Literal["action fail"]
    actionType: actionTypes
    reason: str


class ServerUUIDAssignmentMessage(BaseModel):
    type: Literal["uuid assignment"]
    uuid: str


class ServerSuccessfulReconnectMessage(BaseModel):
    type: Literal["successful reconnect"]


class ServerFailedReconnectionMessage(BaseModel):
    type: Literal["failed reconnect"]
    reason: Literal["invalid uuid", "already connected", "server full"]
    shouldReset: bool


class ServerSendPlayerDataMessage(BaseModel):
    type: Literal["send player data"]

    name: str
    pictureURL: str


class PlayerStatus(BaseModel):
    name: str
    pictureURL: str
    isConnected: bool
    isHost: bool


# Broadcast Messages


class ServerPlayersStatusBroadcast(BaseModel):
    type: Literal["players status"]
    status: List[PlayerStatus]
    state: ServerState


class ServerPDFBroadcast(BaseModel):
    type: Literal["pdf"]
    base64PDF: str
