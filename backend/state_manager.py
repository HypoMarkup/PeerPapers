from shared.message import ServerState

LOBBY_NOT_READY = ServerState.LOBBY_NOT_READY
LOBBY_READY = ServerState.LOBBY_READY
QUESTION = ServerState.QUESTION
MARKING = ServerState.MARKING
WAITING = ServerState.WAITING
GAME_FINISH = ServerState.GAME_FINISH

class StateManager:
    __state: ServerState

    def __init__(self):
        self.__state = LOBBY_NOT_READY

    def get_state(self):
        return self.__state

    def transition_pdf_submitted(self):
        if not self.is_in_lobby():
            raise RuntimeError("Can't set pdf outside of lobby")
        self.__state = LOBBY_READY

    def start(self):
        if self.__state != LOBBY_READY:
            raise RuntimeError("Can't start if Lobby is not ready")
        self.__state = QUESTION

    def to_waiting_room(self):
        # TODO: implementation
        if self.__state not in [MARKING, QUESTION, LOBBY_READY]:
            raise RuntimeError("Can't go to waiting state from this state")
        self.__state = WAITING

    def to_next_marking(self):
        # TODO: implementation
        if self.__state not in [QUESTION, WAITING]:
            raise RuntimeError("Can't go to marking state from this state")
        self.__state = MARKING
    
    def to_next_question(self):
        # TODO: implementation
        if self.__state not in [LOBBY_READY, MARKING, WAITING]:
            raise RuntimeError("Can't go to question state from this state")
        self.__state = QUESTION

    def is_in_lobby(self):
        return self.__state == LOBBY_NOT_READY or self.__state == LOBBY_READY