from managers import player_manager, connection_manager, state_manager, content_manager

def check_question_completion() -> bool :
    if not player_manager.all_players_finished():
        return False

    # TODO: call content manager to handle stored answers then set all players to not finished and change state
    return True