from shared.message import ServerState

isStateLobby = (
    lambda state: state == ServerState.LOBBY_NOT_READY
    or state == ServerState.LOBBY_READY
)
