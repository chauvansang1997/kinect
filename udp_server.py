import socket
import threading


class KinectWebSocket(threading.Thread):
    def __init__(self, queue, configure):
        super().__init__()
        self.connected = set()
        self.queue = queue
        self.server_ip = configure.server_ip
        self.port = configure.port

    async def handler(self, websocket, path):
        self.connected.add(websocket)
        print('client connected')
        while True:
            data = self.queue.get()
            for client in self.connected.copy():
                await client.send(data)

    def send(self):
        udp_client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        while True:
            try:
                data = self.queue.get()
                if data is not None:
                    udp_client_socket.sendto(str.encode(data), (self.server_ip, self.port))
            except Exception as e:
                print(e)

    def run(self):
        self.send()