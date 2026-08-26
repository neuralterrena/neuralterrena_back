import pytest
import asyncio
from config.websocket import websocket_application

@pytest.mark.anyio
async def test_websocket_application():
    receive_queue = asyncio.Queue()
    send_queue = asyncio.Queue()

    async def receive():
        return await receive_queue.get()

    async def send(message):
        await send_queue.put(message)

    scope = {"type": "websocket"}
    task = asyncio.create_task(websocket_application(scope, receive, send))

    await receive_queue.put({"type": "websocket.connect"})
    response = await send_queue.get()
    assert response == {"type": "websocket.accept"}

    await receive_queue.put({"type": "websocket.receive", "text": "ping"})
    response = await send_queue.get()
    assert response == {"type": "websocket.send", "text": "pong!"}

    await receive_queue.put({"type": "websocket.disconnect"})
    await asyncio.wait_for(task, timeout=1.0)
