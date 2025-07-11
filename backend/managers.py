from connectivity import ConnectionManager
from game_state import GameState
from player import PlayerManager


connection_manager = ConnectionManager()
player_manager = PlayerManager()

state: GameState = GameState.Lobby
