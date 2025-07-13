from shared.message import ServerState
from helper import isStateLobby


class StateManager:
    __state: ServerState

    def __init__(self):
        self.__state = ServerState.LOBBY_NOT_READY

    def get_state(self):
        return self.__state

    def transition_pdf_submitted(self):
        if not isStateLobby(self.__state):
            raise RuntimeError("Incorrect transition")
        self.__state = ServerState.LOBBY_READY
