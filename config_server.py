import websockets


class ConfigServer:
    def __init__(self, queue):
        self.connected = set()
        self.queue = queue

    def start_loop(self, loop, server):
        loop.run_until_complete(server)
        loop.run_forever()

    async def handler(self, websocket, path):
        self.connected.add(websocket)
        print('client connected')
        try:
            while True:
                data = self.queue.get()
                if data is not None:
                    await websocket.send(data)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected.remove(websocket)
