"""
This version handles the local agent invocation, creating a agent from 'stm_agent.py'
for each request. FYI we create a new instance per request to ensure that the agent's
memory is properly scoped to the session and actor.
"""

import asyncio
import datetime
import json
import logging
import random

from bedrock_agentcore.memory.session import MemorySessionManager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from julian.stm_agent import create_personal_agent

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

# router = APIRouter(prefix="/api", dependencies=[Depends(validate_jwt)])
MEMORY_ID = "stm_agent_mem-Es6sb6FANG"
REGION = "eu-west-3"
session_manager = MemorySessionManager(memory_id=MEMORY_ID, region_name=REGION)


async def run_agent(user_message: str, session_id: str, actor_id: str) -> dict:
    # create fresh session for this specific request
    user_session = session_manager.create_memory_session(actor_id=actor_id, session_id=session_id)

    # create fresh agent bound to that specific session
    agent = create_personal_agent(memory_session=user_session)

    # run agent wrapped in async block
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, agent, user_message)

    return {"type": "text", "text": result.message}


@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            # Wait for a message from the client. If the client doesn't send,
            # the server will not send anything (no unsolicited messages).
            raw = await websocket.receive_text()
            logger.info("WebSocket received: %s", raw)
            try:
                data = json.loads(raw)
                user_message = data.get("prompt", "")
                session_id = data.get("session_id", "default_session")
                actor_id = data.get("actor_id", "default_user")
                response = await run_agent(user_message, session_id, actor_id)
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
