import asyncio
import websockets

async def hello(uri):
    async with websockets.connect(uri) as websocket:
        await websocket.send("Hello world!")
        while True:
            message = await websocket.recv()
            print(message)

asyncio.get_event_loop().run_until_complete(
    hello('ws://localhost:8000'))