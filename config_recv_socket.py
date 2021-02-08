import json
import socket
import threading

import numpy as np


class ConfigReceiveSocket(threading.Thread):
    def __init__(self, configure):
        super().__init__()
        self.server_ip = configure.config_recv_ip
        self.port = configure.config_recv_port
        self.lock = threading.Lock()
        self.configure = configure

    def recv(self):
        while True:
            try:

                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                print('Socket created')

                s.bind((self.server_ip, self.port))
                s.listen(1)
                conn, addr = s.accept()

                while True:
                    try:
                        data = conn.recv(4096)
                        if data is not None:
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
                            elif config['type'] == 'grid_transform_index':
                                try:
                                    index = config['index']
                                    grid_transform = np.asarray(config['grid_transform']
                                                                , dtype=np.float32)
                                    self.configure.grid_transforms[index] = grid_transform
                                    self.configure.write_grid_transforms()
                                    print('load grid_transform success')
                                except Exception as e:
                                    print(e)
                    except Exception as e:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        print('Socket created')

                        s.bind((self.server_ip, self.port))
                        s.listen(1)
                        conn, addr = s.accept()
                        print(e)
            except Exception as e:
                print(e)

    def run(self):
        self.recv()
