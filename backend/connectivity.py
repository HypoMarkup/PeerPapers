# magic that adds: str | None  =====  Union[str, None], for pre python 3.10
from __future__ import annotations
from abc import ABC, abstractmethod
from types import CoroutineType
from typing import Coroutine, Any, Iterable, Optional, Callable
from fastapi import WebSocket


class CommunicationMedium(ABC):
    @abstractmethod
    def accept(
        self,
        subprotocol: Optional[str] = None,
        headers: Iterable[tuple[bytes, bytes]] | None = None,
    ) -> CoroutineType[Any, Any, None]:
        pass

    @abstractmethod
    def send_text(self, data: str) -> Coroutine[Any, Any, None]:
        pass

    @abstractmethod
    def receive_text(self) -> Coroutine[Any, Any, str]:
        pass

    @abstractmethod
    def close(self) -> Coroutine[Any, Any, None]:
        pass


class WebsocketMedium(CommunicationMedium):
    def __init__(self, ws: WebSocket):
        self.__ws: WebSocket = ws

    def accept(
        self,
        subprotocol: Optional[str] = None,
        headers: Iterable[tuple[bytes, bytes]] | None = None,
    ) -> CoroutineType[Any, Any, None]:
        return self.__ws.accept()

    def send_text(self, data: str) -> Coroutine[Any, Any, None]:
        return self.__ws.send_text(data)

    def receive_text(self) -> Coroutine[Any, Any, str]:
        return self.__ws.receive_text()

    def close(
        self, code: int = 1000, reason: Optional[str] = None
    ) -> Coroutine[Any, Any, None]:
        return self.__ws.close(code, reason)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[CommunicationMedium] = []

    async def connect(self, c: CommunicationMedium):
        await c.accept()
        self.active_connections.append(c)

    def disconnect(self, c: CommunicationMedium):
        self.active_connections.remove(c)

    def filter_connections(self, condition: Callable[[CommunicationMedium], bool]):
        self.active_connections = list(filter(condition, self.active_connections))

    async def send_personal_message(self, c: CommunicationMedium, message: str):
        await c.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
