import asyncio
import datetime
import logging
import random

from fastapi import APIRouter, Depends, FastAPI, WebSocket, WebSocketDisconnect

from jwt_validator import validate_jwt

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api", dependencies=[Depends(validate_jwt)])


async def simulate_processing(message: str) -> str:
    # Simulate variable processing time
    await asyncio.sleep(random.uniform(1, 3))
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Simple helpers to shape the reply
    def _summary(text: str, limit: int = 80) -> str:
        return text if len(text) <= limit else text[: max(0, limit - 3)] + "..."

    def _keywords(text: str, count: int = 5) -> str:
        parts = text.split()
        return " ".join(parts[:count]) if parts else text

    _summary(message, 100)
    _keywords(message, 6)

    templates = [
        # Text Message
        lambda m: {
            "text": f'Hello {now}. Assistant: Received your message: "{_summary(m)}". Nice!',
            "type": "text",
        },
        # Image Message (simulated with a URL)
        lambda m: {
            "text": f"Hello {now}. Assistant: Here's an image related to your message:",
            "type": "image",
            "image_url": "https://placehold.co/150",
        },
        # Video Message (simulated with a URL)
        lambda m: {
            "text": f"Hello {now}. Assistant: Check out this video that might help:",
            "type": "video",
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "thumbnail_url": "https://placehold.co/300x200",
        },
        # Code Snippet Message
        lambda m: {
            "text": f"Hello {now}. Assistant: Here's a code snippet based on your message:",
            "type": "code",
            "code": f"print('You said: {_summary(m)}')",
        },
    ]

    choice = random.choice(templates)
    # Pass full message to templates that use it
    reply = choice(message)
    return reply


@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            # Wait for a message from the client. If the client doesn't send,
            # the server will not send anything (no unsolicited messages).
            data = await websocket.receive_text()
            logger.info("WebSocket received: %s", data)
            try:
                response = await simulate_processing(data)
                await websocket.send_json(response)
            except Exception:
                logger.exception("Error processing message")
                # Attempt to inform client of the error, then continue or close
                try:
                    await websocket.send_text("Error processing message")
                except Exception:
                    pass
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception:
        logger.exception("WebSocket error")
        try:
            await websocket.close()
        except Exception:
            pass
