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

    def set_sock(self, sock):
        self.sock = ref(sock)

    def is_connected(self):
        sock_instance = self.sock()
        return sock_instance is not None
