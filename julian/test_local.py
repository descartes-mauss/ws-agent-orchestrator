import asyncio
import json

import websockets


async def test():
    async with websockets.connect("ws://localhost:8000/") as ws:
        # session + actor ids used for session mgmt, i havent set defaults so keep them
        # test agent is just STM so changeing either will launch new session
        payload = {
            "prompt": "Hello, what else can you help me with?",
            "session_id": "test-session-123",
            "actor_id": "julian",
        }
        await ws.send(json.dumps(payload))
        response = await ws.recv()
        print(json.loads(response))


asyncio.run(test())
