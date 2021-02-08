import json
import pickle
import socket
import struct  ## new
from queue import Queue

import cv2
import numpy as np

HOST = '192.168.0.102'
PORT = 9000
while True:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('Socket created')

        s.bind((HOST, PORT))
        print('Socket bind complete')
        s.listen(10)
        print('Socket now listening')

        conn, addr = s.accept()

        data = b""
        payload_size = struct.calcsize(">L")
        print("payload_size: {}".format(payload_size))
        parameter_data = conn.recv(4096)
        parameter = json.loads(parameter_data)
        grid_transforms = parameter['grid_transforms']

        grid_size_x = parameter['grid_size_x']
        grid_size_y = parameter['grid_size_y']
        width = parameter['width']
        height = parameter['height']

        number_point_x = grid_size_x + 1
        number_point_y = grid_size_y + 1

        item_width = int(width / grid_size_x)
        item_height = int(height / grid_size_y)
        for i in range(0, len(grid_transforms)):
            grid_transform = np.asarray(grid_transforms[i])
            grid_transforms[i] = grid_transform

        current_index = 0
        client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        client_socket.connect(('192.168.0.125', 9000))


        def change_warp_points(event, x, y, flags, param):
            global current_index
            global number_point_x
            global number_point_y
            if event == cv2.EVENT_LBUTTONUP:
                grid_transform[current_index] = [x, y]
                np.savetxt("transform.txt", grid_transform)
                current_index = current_index + 1
                current_index = current_index % (number_point_x * number_point_y)


        cv2.namedWindow('ImageWindow')
        cv2.setMouseCallback('ImageWindow', change_warp_points)

        queue = Queue()


        async def hello(websocket, path):
            while True:
                value = queue.get()
                if value is not None:
                    await websocket.send(value)


        # new_loop = asyncio.new_event_loop()
        # start_server = websockets.serve(hello, "localhost", 9000, loop=new_loop)
        # t = Thread(target=hello, args=(new_loop, start_server))
        # t.start()

        while True:
            while len(data) < payload_size:
                print("Recv: {}".format(len(data)))
                data += conn.recv(4096)

            print("Done Recv: {}".format(len(data)))
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]
            print("msg_size: {}".format(msg_size))
            while len(data) < msg_size:
                data += conn.recv(4096)
            frame_data = data[:msg_size]
            data = data[msg_size:]

            frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            cv2.imshow('ImageWindow', frame)

            image = frame.copy()

            row_pixel = []

            for row in range(0, grid_size_x):
                column_pixel = []
                for column in range(0, grid_size_y):
                    index1 = column * number_point_x + row
                    index2 = column * number_point_x + row + 1
                    index3 = (column + 1) * number_point_x + row
                    index4 = (column + 1) * number_point_x + row + 1

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
            if key == ord('S'):
                value = {'type': 'grid_transform', 'grid_transform': grid_transform.tolist()}
                # queue.put(str.encode(json.dumps(value)))
                client_socket.sendall(str.encode(json.dumps(value)))
    except Exception as e:
        print(e)
