import json
import socket
import threading


class ClientKinectSocket(threading.Thread):
    def __init__(self, configure):
        super().__init__()
        self.port = configure.data_port
        self.configure = configure
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.manage_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def manage_socket(self):
        self.manage_sock.bind(('0.0.0.0', self.port))
        while True:
            try:
                data, address = self.manage_sock.recvfrom(4096)
                client_info = json.loads(data)
                print(client_info)
                self.configure.load_client_config((client_info['client_ip'],
                                                   client_info['client_port']))
                # self.send_sock.sendto(data, (client_info['client_ip'],
                #                              client_info['client_port']))
            except Exception as e:
                print(e)

    def run(self):
        manage_thread = threading.Thread(target=self.manage_socket)
        manage_thread.start()
        while True:
            try:
                for i in range(0, len(self.configure.clients)):
                    data = self.configure.queues[i].get()
                    if data is not None:
                        self.send_sock.sendto(str.encode(data), self.configure.clients[i])
            except Exception as e:
                print(e)
