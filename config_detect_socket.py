import pickle
import socket
import struct
import threading

import cv2


class ConfigDetectSocket(threading.Thread):
    def __init__(self, queue, configure):
        super().__init__()

        self.connected = set()
        self.queue = queue
        self.configure = configure
        self.server_ip = configure.config_detect_ip
        self.port = configure.config_detect_port

    def send(self):
        try:
            self.queue.queues.clear()
            client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            client_socket.connect((self.server_ip, self.port))
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

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
            # self.send()

    def run(self):
        self.send()
