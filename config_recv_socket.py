import json
import socket
import threading

import numpy as np


class ConfigReceiveSocket(threading.Thread):
    def __init__(self, configure):
        super().__init__()
        self.port = configure.config_recv_port
        self.lock = threading.Lock()
        self.configure = configure

    def recv(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('0.0.0.0', self.port))
        print('Socket created')
        while True:
            try:
                data, address = s.recvfrom(4096)
                if data is not None:
                    config = json.loads(data)
                    if config['type'] == 'grid_size_client':
                        try:
                            client_ip = config['client_ip']
                            client_port = config['client_port']
                            grid_size = config['grid_size']
                            self.configure.write_grid_size_client((client_ip, client_port),
                                                                  grid_size)
                        except Exception as e:
                            print(e)
                    elif config['type'] == 'grid_transform_client':
                        try:
                            client_ip = config['client_ip']
                            client_port = config['client_port']
                            grid_transform = np.asarray(config['grid_transform']
                                                        , dtype=np.float32)
                            self.configure.write_transform_client((client_ip, client_port),
                                                                  grid_transform)
                        except Exception as e:
                            print(e)
                    elif config['type'] == 'mesh_transform_client':
                        try:
                            client_ip = config['client_ip']
                            client_port = config['client_port']
                            mesh_transform = np.asarray(config['mesh_transform']
                                                        , dtype=np.float32)
                            self.configure.write_mesh_transform_client((client_ip, client_port),
                                                                       mesh_transform)
                        except Exception as e:
                            print(e)
            except Exception as e:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.bind(('0.0.0.0', self.port))
                print('Socket created')
                print(e)

    def run(self):
        self.recv()
