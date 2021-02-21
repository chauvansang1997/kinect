import socket
import threading


class UdpMeshSocket(threading.Thread):
    def __init__(self, configure):
        super().__init__()
        self.connected = set()
        self.queues = configure.mesh_queues
        self.configure = configure

    async def handler(self, websocket, path):
        self.connected.add(websocket)
        print('client connected')
        while True:
            data = self.queues.get()
            for client in self.connected.copy():
                await client.send(data)

    def send(self):
        udp_client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        while True:
            try:
                for i in range(0, len(self.configure.mesh_queues)):
                    data = self.configure.mesh_queues[i].get()
                    if data is not None:
                        udp_client_socket.sendto(str.encode(data), (self.configure.mesh_clients[i][0],
                                                                    self.configure.mesh_clients[i][1]))
            except Exception as e:
                print(e)

    def run(self):
        self.send()
