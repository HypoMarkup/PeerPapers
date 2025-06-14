from pydantic import BaseModel
from typing import Literal

#
# Client messages
#


class ClientMessage(BaseModel):
    type: Literal["initial connect", "reconnect"]


class ClientConnectMessage(BaseModel):
    type: Literal["initial connect"]


class ClientReconnectMessage(BaseModel):
    type: Literal["reconnect"]
    uuid: str


#
# Server messages
#


class ServerMessage(BaseModel):
    type: Literal["uuid assignment", "successful reconnect", "failed reconnect"]


class ServerUUIDAssignmentMessage(BaseModel):
    type: Literal["uuid assignment"]
    uuid: str


class ServerFailedReconnectionMessage(BaseModel):
    type: Literal["failed reconnect"]
    reason: Literal["invalid uuid", "server full"]
    shouldReset: bool
