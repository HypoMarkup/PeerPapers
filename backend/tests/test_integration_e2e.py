import asyncio

import websockets

from generated.v1.messages_pb2 import (
    ClientMessage,
    CreateRoom,
    ForceEndPhase,
    JoinRoom,
    RequestExamPdf,
    SaveProgress,
    ServerMessage,
    SetReady,
    StartExam,
    SubmitMarking,
    UploadExam,
)
from generated.v1.models_pb2 import (
    MarkingResult,
    RoomSettings,
    RoomState,
    SectionFeedback,
    SubmissionSection,
)
from main import PeerPapersServer


def test_full_multiplayer_exam_lifecycle_e2e() -> None:
    """Simulates 2 real concurrent WebSocket clients playing through the entire exam lifecycle."""

    async def run() -> None:
        test_port = 8799
        server = PeerPapersServer(host="127.0.0.1", port=test_port)
        server_task = asyncio.create_task(server.start())
        await asyncio.sleep(0.05)  # Allow socket to bind

        server_url = f"ws://127.0.0.1:{test_port}"

        try:
            # ─── 1. Alice connects and creates a room ───
            async with websockets.connect(server_url) as ws_alice:
                await ws_alice.send(
                    ClientMessage(
                        create_room=CreateRoom(
                            player_name="Alice",
                            password="test-password",
                            settings=RoomSettings(exam_duration_mins=10),
                        )
                    ).SerializeToString()
                )

                # Alice receives AuthSuccess, RoomCreated, and initial RoomStateUpdate
                auth_alice = ServerMessage.FromString(await ws_alice.recv())
                assert auth_alice.WhichOneof("payload") == "auth_success"

                created_msg = ServerMessage.FromString(await ws_alice.recv())
                assert created_msg.WhichOneof("payload") == "room_created"
                room_code = created_msg.room_created.room_code
                assert len(room_code) == 6

                snap_1 = ServerMessage.FromString(await ws_alice.recv())
                assert snap_1.WhichOneof("payload") == "room_state_update"
                assert snap_1.room_state_update.room.state == RoomState.ROOM_STATE_LOBBY

                # ─── 2. Bob connects and joins the room ───
                async with websockets.connect(server_url) as ws_bob:
                    await ws_bob.send(
                        ClientMessage(
                            join_room=JoinRoom(
                                room_code=room_code,
                                player_name="Bob",
                                password="test-password",
                            )
                        ).SerializeToString()
                    )

                    auth_bob = ServerMessage.FromString(await ws_bob.recv())
                    assert auth_bob.WhichOneof("payload") == "auth_success"

                    snap_bob = ServerMessage.FromString(await ws_bob.recv())
                    assert snap_bob.WhichOneof("payload") == "room_state_update"
                    assert len(snap_bob.room_state_update.room.players) == 2

                    # Alice receives updated snapshot because Bob joined
                    snap_alice_bob_joined = ServerMessage.FromString(await ws_alice.recv())
                    assert len(snap_alice_bob_joined.room_state_update.room.players) == 2

                    # ─── 3. Both players set ready & Alice uploads exam PDF ───
                    await ws_bob.send(ClientMessage(set_ready=SetReady(is_ready=True)).SerializeToString())
                    _ = await ws_bob.recv()    # Bob snapshot
                    _ = await ws_alice.recv()  # Alice snapshot

                    await ws_alice.send(ClientMessage(set_ready=SetReady(is_ready=True)).SerializeToString())
                    _ = await ws_bob.recv()    # Bob snapshot
                    _ = await ws_alice.recv()  # Alice snapshot

                    pdf_bytes = b"%PDF-1.4 Mock exam binary content"
                    await ws_alice.send(
                        ClientMessage(
                            upload_exam=UploadExam(filename="physics.pdf", file_data=pdf_bytes)
                        ).SerializeToString()
                    )
                    _ = await ws_bob.recv()    # Bob snapshot
                    _ = await ws_alice.recv()  # Alice snapshot

                    # ─── 4. Admin starts exam ───
                    await ws_alice.send(ClientMessage(start_exam=StartExam()).SerializeToString())

                    exam_snap_alice = ServerMessage.FromString(await ws_alice.recv())
                    exam_snap_bob = ServerMessage.FromString(await ws_bob.recv())
                    assert exam_snap_alice.room_state_update.room.state == RoomState.ROOM_STATE_EXAM
                    assert exam_snap_bob.room_state_update.room.state == RoomState.ROOM_STATE_EXAM

                    # ─── 5. Bob requests exam PDF & both autosave answers ───
                    await ws_bob.send(ClientMessage(request_exam_pdf=RequestExamPdf()).SerializeToString())
                    pdf_payload = ServerMessage.FromString(await ws_bob.recv())
                    assert pdf_payload.WhichOneof("payload") == "exam_pdf_content"
                    assert pdf_payload.exam_pdf_content.filename == "physics.pdf"
                    assert pdf_payload.exam_pdf_content.file_data == pdf_bytes

                    await ws_alice.send(
                        ClientMessage(
                            save_progress=SaveProgress(
                                section=SubmissionSection(section_index=0, text_data="Alice physics answer")
                            )
                        ).SerializeToString()
                    )
                    await ws_bob.send(
                        ClientMessage(
                            save_progress=SaveProgress(
                                section=SubmissionSection(section_index=0, text_data="Bob physics answer")
                            )
                        ).SerializeToString()
                    )

                    await asyncio.sleep(0.05)  # Ensure background tasks process answers before ending phase

                    # ─── 6. Admin ends exam -> transitions to MARKING ───
                    await ws_alice.send(ClientMessage(force_end_phase=ForceEndPhase()).SerializeToString())

                    # Both receive private MarkingAssignment + updated snapshot
                    alice_assignment = ServerMessage.FromString(await ws_alice.recv())
                    assert alice_assignment.WhichOneof("payload") == "marking_assignment"
                    assert alice_assignment.marking_assignment.author_name == "Bob"

                    alice_marking_snap = ServerMessage.FromString(await ws_alice.recv())
                    assert alice_marking_snap.room_state_update.room.state == RoomState.ROOM_STATE_MARKING

                    bob_assignment = ServerMessage.FromString(await ws_bob.recv())
                    assert bob_assignment.WhichOneof("payload") == "marking_assignment"
                    assert bob_assignment.marking_assignment.author_name == "Alice"

                    bob_marking_snap = ServerMessage.FromString(await ws_bob.recv())
                    assert bob_marking_snap.room_state_update.room.state == RoomState.ROOM_STATE_MARKING

                    # ─── 7. Peer Review: Alice grades Bob (90) and Bob grades Alice (85) ───
                    await ws_alice.send(
                        ClientMessage(
                            submit_marking=SubmitMarking(
                                result=MarkingResult(
                                    sections=[SectionFeedback(section_index=0, score=90, max_score=100)]
                                )
                            )
                        ).SerializeToString()
                    )
                    # Not all marking complete yet -> receives snapshot
                    _ = await ws_alice.recv()
                    _ = await ws_bob.recv()

                    await ws_bob.send(
                        ClientMessage(
                            submit_marking=SubmitMarking(
                                result=MarkingResult(
                                    sections=[SectionFeedback(section_index=0, score=85, max_score=100)]
                                )
                            )
                        ).SerializeToString()
                    )

                    # ─── 8. Automatic Transition to RESULTS ───
                    # Both clients receive ResultsBroadcast followed by final snapshot
                    alice_results = ServerMessage.FromString(await ws_alice.recv())
                    assert alice_results.WhichOneof("payload") == "results_broadcast"
                    results = alice_results.results_broadcast.results
                    assert len(results) == 2
                    assert results[0].player.name == "Bob"
                    assert results[0].total_score == 90
                    assert results[1].player.name == "Alice"
                    assert results[1].total_score == 85

                    alice_final_snap = ServerMessage.FromString(await ws_alice.recv())
                    assert alice_final_snap.room_state_update.room.state == RoomState.ROOM_STATE_RESULTS

                    bob_results = ServerMessage.FromString(await ws_bob.recv())
                    assert bob_results.WhichOneof("payload") == "results_broadcast"

                    bob_final_snap = ServerMessage.FromString(await ws_bob.recv())
                    assert bob_final_snap.room_state_update.room.state == RoomState.ROOM_STATE_RESULTS

        finally:
            server.stop()
            await server_task

    asyncio.run(run())
