"""
Chat API endpoints + WebSocket streaming for RAG-powered conversations.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.core.rag import query_rag, stream_rag
from app.core.llm import generate, stream, generate_with_history, stream_with_history
from app.db.sqlite import get_session
from app.db.models import ChatMessage

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    use_rag: bool = True
    collection: Optional[str] = None
    top_k: int = 5


class ChatResponse(BaseModel):
    answer: str
    sources: list = []
    session_id: str = "default"


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message and get a response (non-streaming)."""
    if req.use_rag:
        result = query_rag(req.message, collection_name=req.collection, top_k=req.top_k)
        answer = result["answer"]
        sources = result["sources"]
    else:
        answer = generate(req.message)
        sources = []

    # Save to chat history
    with get_session() as session:
        session.add(
            ChatMessage(
                session_id=req.session_id,
                role="user",
                content=req.message,
            )
        )
        session.add(
            ChatMessage(
                session_id=req.session_id,
                role="assistant",
                content=answer,
                sources=json.dumps(sources),
            )
        )
        session.commit()

    return ChatResponse(answer=answer, sources=sources, session_id=req.session_id)


@router.get("/chat/history")
async def get_chat_history(session_id: str = "default", limit: int = 50):
    """Get chat history for a session."""
    with get_session() as session:
        messages = (
            session.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )
        messages.reverse()
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "sources": json.loads(m.sources) if m.sources else [],
                "created_at": m.created_at,
            }
            for m in messages
        ]


@router.delete("/chat/history")
async def clear_chat_history(session_id: str = "default"):
    """Clear chat history for a session."""
    with get_session() as session:
        session.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        session.commit()
    return {"status": "cleared", "session_id": session_id}


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for streaming chat responses."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            req = json.loads(data)

            message = req.get("message", "")
            use_rag = req.get("use_rag", True)
            session_id = req.get("session_id", "default")
            collection = req.get("collection")
            top_k = req.get("top_k", 5)

            if not message:
                await websocket.send_text(json.dumps({"error": "Empty message"}))
                continue

            # Save user message
            with get_session() as session:
                session.add(
                    ChatMessage(
                        session_id=session_id,
                        role="user",
                        content=message,
                    )
                )
                session.commit()

            # Stream response
            full_response = ""
            sources = []

            if use_rag:
                token_gen, sources = stream_rag(message, collection_name=collection, top_k=top_k)
                # Send sources first
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "sources",
                            "sources": sources,
                        }
                    )
                )
            else:
                token_gen = stream(message)

            for token in token_gen:
                full_response += token
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "token",
                            "content": token,
                        }
                    )
                )

            # Send completion signal
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "done",
                        "full_response": full_response,
                    }
                )
            )

            # Save assistant message
            with get_session() as session:
                session.add(
                    ChatMessage(
                        session_id=session_id,
                        role="assistant",
                        content=full_response,
                        sources=json.dumps(sources),
                    )
                )
                session.commit()

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({"type": "error", "error": str(e)}))
        except Exception:
            pass
