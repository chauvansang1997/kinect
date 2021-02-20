import json
import pickle
import socket
import struct
import threading

import cv2


class ConfigSendSocket(threading.Thread):
    def __init__(self, queue, configure):
        super().__init__()

        self.connected = set()
        self.queue = queue
        self.configure = configure
        self.server_ip = configure.config_send_ip
        self.port = configure.config_send_port

    def send(self):
        while True:
            try:
                self.queue.queue.clear()
                client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
                client_socket.connect((self.server_ip, self.port))
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
                grid_transforms = []

                for grid_transform in self.configure.grid_transforms:
                    grid_transforms.append(grid_transform.tolist())

                data = {'grid_transforms': grid_transforms,
                        'grid_size_list_x': self.configure.grid_size_list_x,
                        'grid_size_list_y': self.configure.grid_size_list_y,
                        'width': self.configure.width,
                        'height': self.configure.height}
                client_socket.sendall(str.encode(json.dumps(data)))
                while True:
                    try:
                        data = self.queue.get()

                        if data is not None:
                            result, frame = cv2.imencode('.jpg', data, encode_param)

                            data = pickle.dumps(frame, 0)
                            size = len(data)

                            client_socket.sendall(struct.pack(">L", size) + data)
                    except Exception as e:
                        print(e)
                        client_socket.close()
            except Exception as e:
                print(e)
                client_socket.close()

    def run(self):
        self.send()
