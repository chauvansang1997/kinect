import asyncio
import socket
import threading

import websockets


class KinectWebSocket(threading.Thread):

    def __init__(self, queue):
        super().__init__()
        self.connected = set()
        self.queue = queue
        # self.udp_server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        # self.udp_server.bind(('127.0.0.1', 8080))

    # @asyncio.coroutine
    async def handler(self, websocket, path):
        self.connected.add(websocket)
        print('client connected')
        # while True:
        #     pass
        while True:
            data = self.queue.get()
            # data = 'test'
            for client in self.connected.copy():
                await client.send(data)
        # try:
        #
        # except websockets.exceptions.ConnectionClosed as e:
        #     print(e)
        # finally:
        #     self.connected.remove(websocket)

    def send(self):
        UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        while True:
            # if len(self.connected) == 0:
            #         data = self.queue.get()
            # if not self.queue.empty():
            try:
                data = self.queue.get()
                if data is not None:
                    serverAddressPort = ("127.0.0.1", 8080)
                    UDPClientSocket.sendto(str.encode(data), serverAddressPort)
            except Exception as e:
                print(e)
                # if not self.queue.empty():
                #     try:
                #
                #
                #         serverAddressPort = ("127.0.0.1", 8080)
                #
                #         # UDPClientSocket.sendto(str.encode(data), serverAddressPort)
                #     except Exception as e:
                #         print(e)
            #
            # for client in self.connected.copy():
            #     try:
            #         await client.send(data)
            #     except websockets.exceptions.ConnectionClosed as e:
            #         print(e)
            #         self.connected.remove(client)

    def run(self):
        # new_loop = asyncio.new_event_loop()
        #
        # start_server = websockets.serve(self.handler, '0.0.0.0', 8080, loop=new_loop)
        #
        # def start_loop(loop, server):
        #     loop.run_until_complete(server)
        #     loop.run_forever()
        #
        # t = threading.Thread(target=start_loop, args=(new_loop, start_server))
        # t.start()

        # t = threading.Thread(target=self.send, args='')
        # t.start()
        # while True:
        #     print(1)
        self.send()
        # new_loop = asyncio.new_event_loop()
        # new_loop.run_until_complete(self.send())
        # new_loop.run_forever()


class UdpServer(threading.Thread):
    def __init__(self, configure, queue):
        super().__init__()
        self.udp_server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.ip = configure.ip
        self.port = configure.port
        # self.worker = worker
        self.queue = queue

    def handle_request(self, data, address):
        try:
            while True:
                self.udp_server.sendto(str.encode(data), address)
        except Exception as e:
            print(e)

    def run(self):
        self.udp_server.bind((self.ip, self.port))

        while True:
            try:
                _, address = self.udp_server.recvfrom(1024)
                data = self.queue.get()
                c_thread = threading.Thread(target=self.handle_request,
                                            args=(data, address))
                c_thread.daemon = True
                c_thread.start()
            except Exception as e:
                self.udp_server.close()
                self.udp_server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
                self.udp_server.bind((self.ip, self.port))
                print(e)
