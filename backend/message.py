from pydantic import BaseModel
from typing import Literal


class IncomingMessage(BaseModel):
    type: Literal["acquireUUID", "checkUUID"]


class CheckUUIDMessage(BaseModel):
    type: Literal["checkUUID"]
    uuid: str


class OutgoingMessage(BaseModel):
    type: Literal["assignUUID", "validUUID", "invalidUUID"]


class AssignUUIDMessage(BaseModel):
    type: Literal["assignUUID"]
    uuid: str
