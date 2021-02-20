import json
import socket
import struct  ## new
from queue import Queue

import cv2
import numpy as np

MAX_DGRAM = 2 ** 16
HOST = '192.168.0.103'
PORT = 9000
server_ip = '192.168.0.126'
config_client_ip = '192.168.0.101'
config_client_port = 8081
server_port = 9003
server_rev_port = 9002


def dump_buffer(s):
    """ Emptying buffer frame """
    while True:
        seg, addr = s.recvfrom(MAX_DGRAM)
        print(seg[0])
        if struct.unpack("B", seg[0:1])[0] == 1:
            print("finish emptying buffer")
            break


while True:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ping_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = str.encode(json.dumps({'client_ip': HOST,
                                         'client_port': PORT,
                                         'config_client_ip': config_client_ip,
                                         'config_client_port': config_client_port,
                                         'type': 'mesh'}))
        ping_socket.sendto(message, (server_ip, server_port))
        print('Socket created')

        s.bind((HOST, PORT))
        print('Socket now listening')

        parameter_data, _ = s.recvfrom(4096)
        parameter = json.loads(parameter_data)
        mesh_transforms = parameter['mesh_transforms']

        for i in range(0, len(mesh_transforms)):
            mesh_transform = np.asarray(mesh_transforms[i])
            mesh_transforms[i] = mesh_transform

        current_index = 0
        current_server_index = 0

        client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        def change_warp_points(event, x, y, flags, param):
            global current_index
            global mesh_transforms
            global current_server_index
            if event == cv2.EVENT_LBUTTONUP:
                mesh_transforms[current_server_index][current_index] = [x, y]
                np.savetxt("mesh_transform.txt", mesh_transforms[current_server_index][current_index])
                current_index = current_index + 1
                current_index = current_index % 4


        cv2.namedWindow('ImageWindow')
        cv2.setMouseCallback('ImageWindow', change_warp_points)

        queue = Queue()

        data = b''
        dump_buffer(s)
        while True:
            seg, addr = s.recvfrom(MAX_DGRAM)
            if struct.unpack("B", seg[0:1])[0] > 1:
                data += seg[1:]
            else:
                data += seg[1:]
                frame = cv2.imdecode(np.fromstring(data, dtype=np.uint8), 1)
                cv2.imshow('frame', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                data = b''

                cv2.imshow('ImageWindow', frame)

                image = frame.copy()

                row_pixel = []

                mesh_transform = mesh_transforms[current_server_index]

                M = cv2.getPerspectiveTransform(mesh_transform,
                                                np.float32([[0, 0],
                                                            [512, 0],
                                                            [0, 424],
                                                            [512, 424]]))
                mesh_transform = cv2.warpPerspective(mesh_transform, M, (512, 424))

                cv2.imshow('mesh_transform', mesh_transform)
                key = cv2.waitKey(delay=1)
                # print("send success")
                if key == ord('S'):
                    value = {'type': 'mesh_transform_client',
                             'client_ip': config_client_ip,
                             'client_port': config_client_port,
                             'mesh_transform': mesh_transforms[current_server_index].tolist()}
                    client_socket.sendto(str.encode(json.dumps(value)),
                                         (server_ip, server_rev_port))
                    print("send success")
                # if key == ord('='):
                #     current_index = 0
                #     current_server_index = current_server_index + 1
                #     current_server_index = current_server_index % len(grid_size_list[0])
                # if key == ord('-'):
                #     current_index = 0
                #     current_server_index = current_server_index - 1
                #     if current_server_index < 0:
                #         current_server_index = len(grid_size_list[0]) - 1
    except Exception as e:
        print(e)
