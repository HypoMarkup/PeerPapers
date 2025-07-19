import uuid
from connectivity import CommunicationMedium
from weakref import ref, ReferenceType
from typing import Optional, Callable

weakSock = ReferenceType[CommunicationMedium]


class Player:
    sock: weakSock

    name: str
    pictureURL: str
    is_initialised: bool
    is_finished: bool

    def __init__(self, sock: CommunicationMedium):
        self.uuid: str = self.generate_UUID()
        self.set_sock(sock)

        self.name = ""
        self.pictureURL = ""
        self.is_initialised = False
        self.is_finished = False

    def set_data(self, name: str, pictureURL: str):
        self.is_initialised = True
        self.name = name
        self.pictureURL = pictureURL

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

    def check_finished(self):
        return self.is_finished


    def __repr__(self) -> str:
        return f"{self.uuid} {self.sock()}"


class PlayerManager:
    def __init__(self) -> None:
        self.players: list[Player] = []
        self.__host: Optional[Player] = None

    def valid_players(self):
        return list(filter(lambda x: x.is_initialised, self.players))

    def number_of_players(self):
        return len(self.valid_players())

    def add_player(self, p: Player):
        self.players.append(p)
        if self.__host == None:
            self.__host = p

    def remove_player(self, p: Player):
        self.players.remove(p)

        if p == self.__host:
            self.__host = self.players[0] if len(self.players) != 0 else None

    async def broadcast(self, message: str):
        for player in self.players:
            sock = player.get_sock()
            if sock is not None and player.is_initialised:
                await sock.send_text(message)

    def get_player(self, condition: Callable[[Player], bool]):
        for i in self.players:
            if condition(i):
                return i
        return None

    def filter_players(self, condition: Callable[[Player], bool]):
        to_remove = filter(lambda x: not condition(x), self.players)
        self.players = list(filter(condition, self.players))
        return to_remove

    def get_player_by_connection(self, c: CommunicationMedium):
        return self.get_player(lambda x: x.get_sock() == c)

    def get_host(self):
        return self.__host

    def all_players_finished(self):
        return all(p.check_finished() for p in self.players if p.is_initialised)

    def unready_all_players(self):
        for p in self.valid_players():
            p.is_finished = False