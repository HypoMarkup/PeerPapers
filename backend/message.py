from pydantic import BaseModel
from typing import Literal


class IncomingMessage(BaseModel):
    type: Literal["initial-connect", "reconnect"]


class InitialConnectMessage(BaseModel):
    type: Literal["initial-connect"]


class ReconnectMessage(BaseModel):
    type: Literal["reconnect"]
    uuid: str


class OutgoingMessage(BaseModel):
    type: Literal["uuid-assignment", "successful-reconnect", "failed-reconnect"]


class UUIDAssignmentMessage(BaseModel):
    type: Literal["uuid-assignment"]
    uuid: str
