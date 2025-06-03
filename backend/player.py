import uuid
from connectivity import CommunicationMedium
from weakref import ref, ReferenceType

weakSock = ReferenceType[CommunicationMedium]


class Player:
    sock: weakSock

    def __init__(self, sock: CommunicationMedium):
        self.uuid: str = self.generate_UUID()
        self.set_sock(sock)

    def generate_UUID(self) -> str:
        # uuid4 is random
        return str(uuid.uuid4())

    def set_sock(self, sock: CommunicationMedium):
        self.sock = ref(sock)

    def is_connected(self):
        sock_instance = self.sock()
        return sock_instance is not None

    def __repr__(self) -> str:
        return f"{self.uuid} {self.sock()}"
        pass


class PlayerManager:
    def __init__(self) -> None:
        self.players: list[Player] = []

    def add_player(self, p: Player):
        self.players.append(p)

    def reconnect_player_via_UUID(self, uuid: str, c: CommunicationMedium) -> bool:
        for p in self.players:
            if p.uuid == uuid:
                if not p.is_connected():
                    p.set_sock(c)
                    return True
                else:
                    # TODO: Handle this
                    print("Player is already connected")
        return False
