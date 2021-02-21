import json
import math
import socket
import struct
import threading
import cv2


class FrameSegment(threading.Thread):
    """
    Object to break down image frame segment
    if the size of image exceed maximum datagram size
    """
    MAX_DGRAM = 2 ** 16
    MAX_IMAGE_DGRAM = MAX_DGRAM - 64  # extract 64 bytes in case UDP frame overflown

    def __init__(self, configure, image_queue):
        threading.Thread.__init__(self)
        self.manage_port = configure.config_manage_config_port
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.manage_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.configure = configure
        self.queue = image_queue
        self.clients = []

    def udp_frame(self, img, client):
        """
        Compress image and Break down
        into data segments
        """
        compress_img = cv2.imencode('.jpg', img)[1]
        dat = compress_img.tostring()
        size = len(dat)
        count = math.ceil(size / self.MAX_IMAGE_DGRAM)
        array_pos_start = 0
        while count:
            array_pos_end = min(size, array_pos_start + self.MAX_IMAGE_DGRAM)
            self.send_sock.sendto(struct.pack("B", count) +
                                  dat[array_pos_start:array_pos_end],
                                  client
                                  )
            array_pos_start = array_pos_end
            count -= 1

    def manage_socket(self):
        self.manage_sock.bind(('0.0.0.0', self.manage_port))
        while True:
            try:
                data, address = self.manage_sock.recvfrom(1024)
                client_info = json.loads(data)
                config_client = (client_info['config_client_ip'],
                                 client_info['config_client_port'])
                client_address = (client_info['client_ip'],
                                  client_info['client_port'])
                if client_info['type'] == 'mesh':
                    mesh_transform = self.configure.get_mesh_client_config(config_client)
                    data = {'mesh_transform': [mesh_transform.tolist()]}
                    self.manage_sock.sendto(str.encode(json.dumps(data)), client_address)
                else:
                    self.configure.write_grid_size_client(config_client, client_info['grid_size'])
                    grid_transform, grid_size = self.configure.get_client_config(config_client)
                    data = {'grid_transforms': [grid_transform.tolist()],
                            'grid_size_list': [grid_size.tolist()],
                            'width': self.configure.width,
                            'height': self.configure.height}
                    self.manage_sock.sendto(str.encode(json.dumps(data)), client_address)
                if client_address not in self.clients:
                    self.clients.append(client_address)
            except Exception as e:
                print(e)

    def run(self):
        manage_thread = threading.Thread(target=self.manage_socket)
        manage_thread.start()
        while True:
            try:
                data = self.queue.get()
                if data is not None:
                    for client in self.clients:
                        self.udp_frame(data, client)
            except Exception as e:
                print(e)
