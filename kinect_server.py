import websockets


class KinectServer:
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
                # str_points = json.dumps(data)
                for client in self.connected.copy():
                    await client.send(data)
                # if self.kinect_worker.available_data:
                #     data = self.kinect_worker.data
                #     str_points = json.dumps(data)
                #     for client in self.connected.copy():
                #         await client.handle_request(str_points)
                #     # print(str_points)
                #     self.kinect_worker.available_data = False
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected.remove(websocket)
