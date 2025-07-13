from connectivity import ConnectionManager
from player import PlayerManager
from shared.message import ServerState
from typing import Optional
from state_manager import StateManager
from content_manager import ContentManager


connection_manager = ConnectionManager()
player_manager = PlayerManager()

state_manager: StateManager = StateManager()
content_manager: ContentManager = ContentManager()
