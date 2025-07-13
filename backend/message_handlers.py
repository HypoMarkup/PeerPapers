from typing import Optional
from validators import is_valid_name
from connectivity import CommunicationMedium
from player import Player
from managers import player_manager, state_manager, content_manager
from shared.message import (
    ClientSetPlayerDataMessage,
    ServerActionFailMessage,
    ServerActionSuccessMessage,
    ServerSendPlayerDataMessage,
    ServerUUIDAssignmentMessage,
    ClientReconnectMessage,
    ServerMessage,
    ServerFailedReconnectionMessage,
    ClientHostSetPDF,
    ServerState,
)
from helper import isStateLobby

# Authenticated messages are messages which can only be made by clients with a player object
# Host messages are authenticated messages which can only be made by the host

# Every handler should follow the following rules

# Unauthenticated
# Parameters:
# data: str, p: Optional[Player], c: CommunicationMedium
# Return Tuple:
# p: Optional[Player], message: Optional[str], code: Optional[int], reason: Optional[str]

# Authenticated + Host
# Parameters:
# data: str, p: Player
# Return Tuple:
# message: Optional[str], code: Optional[int], reason: Optional[str]

# If code and reason are not None, then an exception is raised and the socket disconnected
# Message will be sent before socket is disconnected


def handle_initial_connect(
    _: str, p: Optional[Player], c: CommunicationMedium
) -> tuple[Optional[Player], Optional[str], Optional[int], Optional[str]]:
    if p is not None:
        return (None, "", 1003, "Already connected")

    p = Player(c)
    player_manager.add_player(p)
    outgoing_msg = ServerUUIDAssignmentMessage(type="uuid assignment", uuid=p.uuid)
    return (p, outgoing_msg.model_dump_json(), None, None)


def handle_reconnect(
    data: str, p: Optional[Player], c: CommunicationMedium
) -> tuple[Optional[Player], Optional[str], Optional[int], Optional[str]]:
    if p is not None:
        return (None, "", 1003, "Already connected")

    incoming_msg = ClientReconnectMessage.model_validate_json(data)
    p = player_manager.get_player(lambda x: x.uuid == incoming_msg.uuid)

    if p is None:
        outgoing_msg = ServerFailedReconnectionMessage(
            type="failed reconnect",
            reason="invalid uuid",
            shouldReset=(isStateLobby(state_manager.get_state())),
        )
        return (None, outgoing_msg.model_dump_json(), 1003, "Invalid uuid")

    if p.is_connected():
        outgoing_msg = ServerFailedReconnectionMessage(
            type="failed reconnect",
            reason="already connected",
            shouldReset=False,
        )
        return (None, outgoing_msg.model_dump_json(), 1003, "Already connected")

    p.set_sock(c)

    return (
        p,
        ServerMessage(type="successful reconnect").model_dump_json(),
        None,
        None,
    )


# Authenticated messages


def handle_get_player_data(
    _: str, p: Player
) -> tuple[Optional[str], Optional[int], Optional[str]]:
    return (
        ServerSendPlayerDataMessage(
            type="send player data", name=p.name, pictureURL=p.pictureURL
        ).model_dump_json(),
        None,
        None,
    )


def handle_set_player_data(
    data: str, p: Player
) -> tuple[Optional[str], Optional[int], Optional[str]]:
    incoming_msg = ClientSetPlayerDataMessage.model_validate_json(data)
    new_name = incoming_msg.name.lower()

    player_with_this_name = player_manager.get_player(lambda x: x.name == new_name)

    if not is_valid_name(new_name):
        return (
            ServerActionFailMessage(
                type="action fail",
                actionType="set player data",
                reason="This name is not valid",
            ).model_dump_json(),
            None,
            None,
        )

    if player_with_this_name != None and player_with_this_name != p:
        return (
            ServerActionFailMessage(
                type="action fail",
                actionType="set player data",
                reason="This name is taken",
            ).model_dump_json(),
            None,
            None,
        )

    p.name = new_name
    p.pictureURL = incoming_msg.pictureURL
    return (
        ServerActionSuccessMessage(
            type="action success", actionType="set player data"
        ).model_dump_json(),
        None,
        None,
    )


# Host messages


def handle_host_set_PDF(
    data: str, _: Player
) -> tuple[Optional[str], Optional[int], Optional[str]]:
    incoming_msg = ClientHostSetPDF.model_validate_json(data)

    # TODO: Validate pdf base64
    content_manager.set_pdf(incoming_msg.base64PDF)
    content_manager.set_number_of_questions(incoming_msg.numberOfQuestions)

    try:
        state_manager.transition_pdf_submitted()

        return (
            ServerActionSuccessMessage(
                type="action success", actionType="host set pdf"
            ).model_dump_json(),
            None,
            None,
        )
    except RuntimeError as e:
        return (
            None,
            1008,
            str(e),
        )


def handle_host_start(
    data: str, _: Player
) -> tuple[Optional[str], Optional[int], Optional[str]]:
    try:
        state_manager.start()
        return (None, None, None)
    except RuntimeError as e:
        return (
            None,
            1008,
            str(e),
        )
