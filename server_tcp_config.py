import pickle
import socket
import struct
import cv2


class TcpReceiveImage:
    def __init__(self, server_socket):
        self.socket = server_socket
        # self.socket.bind((host, port))
        self.socket.listen(10)
        self.data = b""
        self.connection, address = self.socket.accept()
        self.payload_size = struct.calcsize(">L")
        print("payload_size: {}".format(self.payload_size))

    def receive(self):
        while len(self.data) < self.payload_size:
            self.data += self.connection.recv(4096)
        self.data = self.data[self.payload_size:]
        msg_size = struct.unpack(">L", self.data[:self.payload_size])[0]

        while len(self.data) < msg_size:
            self.data += self.connection.recv(4096)

        frame_data = self.data[:msg_size]
        self.data = self.data[msg_size:]

        stream_image = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
        stream_image = cv2.imdecode(stream_image, cv2.IMREAD_COLOR)
        return stream_image


host = '0.0.0.0'
PORT = 8485
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_receive_image = TcpReceiveImage(s)
while True:
    frame = tcp_receive_image.receive()
    cv2.imshow('ImageWindow', frame)

    cv2.waitKey(1)
