import uuid
from connectivity import CommunicationMedium
from weakref import ref, ReferenceType
from typing import Optional, Callable

weakSock = ReferenceType[CommunicationMedium]


class Player:
    sock: weakSock

    name: str
    pictureURL: str
    is_host: bool

    def __init__(self, sock: CommunicationMedium):
        self.uuid: str = self.generate_UUID()
        self.set_sock(sock)

        self.name = ""
        self.pictureURL = ""
        self.is_host = False

    def generate_UUID(self) -> str:
        # uuid4 is random
        return str(uuid.uuid4())

    def set_sock(self, sock: CommunicationMedium):
        self.sock = ref(sock)

    def get_sock(self):
        return self.sock()

    def is_connected(self):
        sock_instance = self.sock()
        return sock_instance is not None

    def __repr__(self) -> str:
        return f"{self.uuid} {self.sock()}"


class PlayerManager:
    def __init__(self) -> None:
        self.players: list[Player] = []

    def add_player(self, p: Player):
        self.players.append(p)

    def remove_player(self, p: Player):
        self.players.remove(p)

    def reconnect_player_via_UUID(
        self, uuid: str, c: CommunicationMedium
    ) -> Optional[Player]:
        for p in self.players:
            if p.uuid == uuid:
                if not p.is_connected():
                    p.set_sock(c)
                    return p
                else:
                    # TODO: Handle this
                    print("Player is already connected")
        return None

    async def broadcast(self, message: str):
        for player in self.players:
            sock = player.get_sock()
            if sock is not None:
                await sock.send_text(message)

    def get_player(self, condition: Callable[[Player], bool]):
        for i in self.players:
            if condition(i):
                return i
        return None

    def filter_players(self, condition: Callable[[Player], bool]):
        self.players = list(filter(condition, self.players))

    def get_player_by_connection(self, c: CommunicationMedium):
        return self.get_player(lambda x: x.get_sock() == c)
