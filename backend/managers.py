from connectivity import ConnectionManager
from player import PlayerManager
from shared.message import ServerState
from typing import Optional


connection_manager = ConnectionManager()
player_manager = PlayerManager()

state: ServerState = ServerState.LOBBY_NOT_READY

base64PDF: Optional[str] = None
