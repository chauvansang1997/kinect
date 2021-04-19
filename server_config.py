import json
import socket
import struct  ## new
from queue import Queue

import cv2
import numpy as np

MAX_DGRAM = 2 ** 16
HOST = '192.168.0.110'
PORT = 9000
server_ip = '192.168.0.123'
config_client_ip = '192.168.0.101'
config_client_port = 8089
server_port = 9003
server_rev_port = 9002
grid_size = [3, 1]

value = {'type': 'grid_size_client',
         'client_ip': config_client_ip,
         'client_port': config_client_port,
         'grid_size': grid_size}
client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)


# client_socket.sendto(str.encode(json.dumps(value)),
#                      (server_ip, server_rev_port))


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
                                         'type': 'throw_ball', 'grid_size': grid_size}))

        ping_socket.sendto(message, (server_ip, server_port))
        print('Socket created')

        s.bind((HOST, PORT))
        print('Socket now listening')

        parameter_data, _ = s.recvfrom(4096)
        parameter = json.loads(parameter_data)
        grid_transforms = parameter['grid_transforms']

        grid_size_list = parameter['grid_size_list']

        width = parameter['width']
        height = parameter['height']

        item_width_list = []
        item_height_list = []
        for i in range(0, len(grid_transforms)):
            item_width_list.append(int(width / grid_size_list[i][0]))
            item_height_list.append(int(height / grid_size_list[i][1]))

        for i in range(0, len(grid_transforms)):
            grid_transform = np.asarray(grid_transforms[i])
            grid_transforms[i] = grid_transform

        current_index = 0
        current_server_index = 0


        # client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        def change_warp_points(event, x, y, flags, param):
            global current_index
            global grid_size_list
            global grid_transforms
            global current_server_index
            if event == cv2.EVENT_LBUTTONUP:
                grid_transforms[current_server_index][current_index] = [x, y]
                np.savetxt("transform.txt", grid_transforms[current_server_index][current_index])
                current_index = current_index + 1
                current_index = current_index % ((grid_size_list[current_server_index][0] + 1)
                                                 * (grid_size_list[current_server_index][1] + 1))


        cv2.namedWindow('ImageWindow')
        cv2.setMouseCallback('ImageWindow', change_warp_points)

        queue = Queue()

        # new_loop = asyncio.new_event_loop()
        # start_server = websockets.serve(hello, "localhost", 9000, loop=new_loop)
        # t = Thread(target=hello, args=(new_loop, start_server))
        # t.start()
        data = b''
        dump_buffer(s)
        while True:
            seg, addr = s.recvfrom(MAX_DGRAM)
            print(addr)
            if addr[0] != server_ip:
                continue
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

                grid_transform = grid_transforms[current_server_index]
                grid_size = grid_size_list[current_server_index]
                item_width = item_width_list[current_server_index]
                item_height = item_height_list[current_server_index]
                for row in range(0, grid_size[0]):
                    column_pixel = []
                    for column in range(0, grid_size[1]):
                        index1 = column * (grid_size[0] + 1) + row
                        index2 = column * (grid_size[0] + 1) + row + 1
                        index3 = (column + 1) * (grid_size[0] + 1) + row
                        index4 = (column + 1) * (grid_size[0] + 1) + row + 1

                        m2 = cv2.getPerspectiveTransform(
                            np.float32(
                                [(grid_transform[index1][0], grid_transform[index1][1]),
                                 (grid_transform[index2][0], grid_transform[index2][1]),
                                 (grid_transform[index3][0], grid_transform[index3][1]),
                                 (grid_transform[index4][0], grid_transform[index4][1])]),
                            np.float32(
                                [(0, 0),
                                 (item_width, 0),
                                 (0, item_height),
                                 (item_width, item_height)]
                            ),
                        )
                        m2 = cv2.warpPerspective(image, m2, (item_width, item_height))

                        if column == 0:
                            column_pixel = m2
                        else:
                            column_pixel = np.concatenate((column_pixel, m2), axis=0)

                    if row == 0:
                        row_pixel = column_pixel
                    else:
                        row_pixel = np.concatenate((row_pixel, column_pixel), axis=1)

                cv2.imshow('row_pixel', row_pixel)
                key = cv2.waitKey(delay=1)
                # print("send success")
                if key == ord('S'):
                    value = {'type': 'grid_transform_client',
                             'client_ip': config_client_ip,
                             'client_port': config_client_port,
                             'grid_transform': grid_transforms[current_server_index].tolist()}
                    client_socket.sendto(str.encode(json.dumps(value)),
                                         (server_ip, server_rev_port))
                    print("send success")
                if key == ord('='):
                    current_index = 0
                    current_server_index = current_server_index + 1
                    current_server_index = current_server_index % len(grid_size_list[0])
                if key == ord('-'):
                    current_index = 0
                    current_server_index = current_server_index - 1
                    if current_server_index < 0:
                        current_server_index = len(grid_size_list[0]) - 1
    except Exception as e:
        print(e)
