import json
import threading

import numpy as np
import websockets


class KinectServer(threading.Thread):
    def __init__(self, configure):
        super().__init__()
        self.connected = set()
        self.configure = configure

    def start_loop(self, loop, server):
        loop.run_until_complete(server)
        loop.run_forever()

    async def handler(self, websocket, path):
        self.connected.add(websocket)
        print('client connected')
        try:
            while True:
                data = await websocket.recv()
                print(data)

                config = json.loads(data)
                if config['type'] == 'grid_size':
                    try:
                        self.configure.grid_size_x = config['grid_size_x']
                        self.configure.grid_size_y = config['grid_size_y']
                        self.configure.write()
                        print('load grid_size success')
                    except Exception as e:
                        print(e)
                elif config['type'] == 'wrap_transform':
                    try:
                        self.configure.wrap_transform = config['wrap_transform']
                        self.configure.write_wrap_transform()
                        print('load wrap_transform success')
                    except Exception as e:
                        print(e)
                elif config['type'] == 'grid_transform':
                    try:
                        self.configure.grid_transform = np.asarray(config['grid_transform']
                                                                   , dtype=np.float32)
                        self.configure.write_grid_transform(self.configure.grid_transform)
                        print('load grid_transform success')
                    except Exception as e:
                        print(e)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected.remove(websocket)

    def run(self):
        from websocket import create_connection
        while True:
            try:
                ws = create_connection("ws://127.0.0.1:9000")
                while True:
                    try:
                        result = ws.recv()
                        config = json.loads(result)
                        if config['type'] == 'grid_size':
                            try:
                                self.configure.grid_size_x = config['grid_size_x']
                                self.configure.grid_size_y = config['grid_size_y']
                                self.configure.write()
                                print('load grid_size success')
                            except Exception as e:
                                print(e)
                        elif config['type'] == 'wrap_transform':
                            try:
                                self.configure.wrap_transform = config['wrap_transform']
                                self.configure.write_wrap_transform()
                                print('load wrap_transform success')
                            except Exception as e:
                                print(e)
                        elif config['type'] == 'grid_transform':
                            try:
                                self.configure.grid_transform = np.asarray(config['grid_transform']
                                                                           , dtype=np.float32)
                                self.configure.write_grid_transform(self.configure.grid_transform)
                                print('load grid_transform success')
                            except Exception as e:
                                print(e)
                    except Exception as e:
                        print(e)
                ws.close()
            except Exception as e:
                print(e)
