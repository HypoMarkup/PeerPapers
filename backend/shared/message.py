from pydantic import BaseModel
from typing import Literal

#
# Player data
#


class PlayerData(BaseModel):
    name: str

    # URL
    picture: str


#
# Client messages
#


class ClientMessage(BaseModel):
    type: Literal["initial connect", "reconnect", "set player data", "get player data"]


class ClientConnectMessage(BaseModel):
    type: Literal["initial connect"]


class ClientReconnectMessage(BaseModel):
    type: Literal["reconnect"]
    uuid: str


class ClientSetPlayerDataMessage(BaseModel):
    type: Literal["set player data"]
    data: PlayerData


#
# Server messages
#


class ServerMessage(BaseModel):
    type: Literal[
        "uuid assignment",
        "successful reconnect",
        "failed reconnect",
        "send player data",
        "invalid player data",
    ]


class ServerUUIDAssignmentMessage(BaseModel):
    type: Literal["uuid assignment"]
    uuid: str


class ServerSuccessfulReconnectMessage(BaseModel):
    type: Literal["successful reconnect"]


class ServerFailedReconnectionMessage(BaseModel):
    type: Literal["failed reconnect"]
    reason: Literal["invalid uuid", "server full"]
    shouldReset: bool


class ServerSendPlayerData(BaseModel):
    type: Literal["send player data"]
    data: PlayerData
