import socketio
from app.websocket.chat_handler import connected_users


def register_video_handlers(sio: socketio.AsyncServer):

    @sio.event
    async def call_user(sid, data):
        """Initiate a video call."""
        session = await sio.get_session(sid)
        if not session:
            return

        target_user_id = data.get("target_user_id")
        offer = data.get("offer")
        caller_id = session["user_id"]

        if target_user_id in connected_users:
            await sio.emit(
                "incoming_call",
                {"caller_id": caller_id, "offer": offer},
                to=connected_users[target_user_id],
            )
        else:
            await sio.emit(
                "call_failed",
                {"reason": "Utilizatorul nu este online"},
                to=sid,
            )

    @sio.event
    async def answer_call(sid, data):
        """Answer a video call."""
        session = await sio.get_session(sid)
        if not session:
            return

        caller_id = data.get("caller_id")
        answer = data.get("answer")
        answerer_id = session["user_id"]

        if caller_id in connected_users:
            await sio.emit(
                "call_answered",
                {"answerer_id": answerer_id, "answer": answer},
                to=connected_users[caller_id],
            )

    @sio.event
    async def ice_candidate(sid, data):
        """Exchange ICE candidates for WebRTC."""
        session = await sio.get_session(sid)
        if not session:
            return

        target_user_id = data.get("target_user_id")
        candidate = data.get("candidate")

        if target_user_id in connected_users:
            await sio.emit(
                "ice_candidate",
                {"candidate": candidate, "from_user_id": session["user_id"]},
                to=connected_users[target_user_id],
            )

    @sio.event
    async def end_call(sid, data):
        """End a video call."""
        session = await sio.get_session(sid)
        if not session:
            return

        target_user_id = data.get("target_user_id")

        if target_user_id in connected_users:
            await sio.emit(
                "call_ended",
                {"user_id": session["user_id"]},
                to=connected_users[target_user_id],
            )
