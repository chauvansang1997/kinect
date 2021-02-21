import json
import socket
import threading

lock = threading.Lock()

class ClientKinectSocket(threading.Thread):
    def __init__(self, configure):
        super().__init__()
        self.port = configure.data_port
        self.configure = configure
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_mesh_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.manage_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def manage_socket(self):
        self.manage_sock.bind(('0.0.0.0', self.port))
        while True:
            try:
                data, address = self.manage_sock.recvfrom(4096)
                lock.acquire()
                client_info = json.loads(data)
                # print(client_info)
                if client_info['type'] == 'mesh':
                    self.configure.load_mesh_config((client_info['client_ip'],
                                                     client_info['client_port']))
                else:
                    self.configure.load_client_config((client_info['client_ip'],
                                                       client_info['client_port']))
                lock.release()
            except Exception as e:
                print(e)
                print('load data error')

    def run(self):
        manage_thread = threading.Thread(target=self.manage_socket)
        manage_thread.start()
        send_grid_thread = threading.Thread(target=self.send_grid)
        send_grid_thread.start()
        self.send_mesh()

    def send_mesh(self):
        while True:
            try:
                for i in range(0, len(self.configure.mesh_clients)):
                    data = self.configure.mesh_queues[i].get()
                    if data is not None:
                        self.send_mesh_sock.sendto(str.encode(data), self.configure.mesh_clients[i])
            except Exception as e:
                print(e)

    def send_grid(self):
        while True:
            try:
                for i in range(0, len(self.configure.clients)):
                    data = self.configure.queues[i].get()
                    if data is not None:
                        self.send_sock.sendto(str.encode(data), self.configure.clients[i])
            except Exception as e:
                print(e)
