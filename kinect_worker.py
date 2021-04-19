import json
import threading

import cv2
import numpy as np
from pylibfreenect2 import Freenect2, SyncMultiFrameListener, FrameType, Registration, Frame
from pylibfreenect2 import setGlobalLogger


class KinectWorker:
    def __init__(self, configure, image_queue, detect_queue):
        self.grid_size_list = configure.grid_size_list
        self.listener = SyncMultiFrameListener(
            FrameType.Color | FrameType.Ir | FrameType.Depth)
        self.available_data = False
        self.close = False
        self.configure = configure
        self.min_depth = int(configure.min_depth)
        self.max_depth = int(configure.max_depth)
        self.kernel = int(configure.kernel)
        self.first_depth = configure.first_depth
        self.area = int(configure.area)

        self.index = 0
        self.queues = configure.queues
        self.detect_queue = detect_queue
        self.image_queue = image_queue
        self.mesh_queues = configure.mesh_queues
        self.item_width_list = []
        self.item_height_list = []
        self.color_pixel_list = []
        self.new_depth_list = []
        self.color_row_pixel_list = []
        self.row_pixel_list = []
        self.matrix_transforms = []

    def run(self):
        configure = self.configure
        width = configure.width
        height = configure.height
        self.matrix_transforms = []
        self.item_width_list = []
        self.item_height_list = []
        self.color_pixel_list = []
        self.new_depth_list = []
        self.color_row_pixel_list = []
        self.row_pixel_list = []
        for i in range(0, len(configure.clients)):
            self.item_width_list.append(int(width / self.grid_size_list[i][0]))
            self.item_height_list.append(int(height / self.grid_size_list[i][1]))
            self.color_pixel_list.append([])
            self.new_depth_list.append([])
            self.color_row_pixel_list.append([])
            self.row_pixel_list.append([])
        try:
            from pylibfreenect2 import OpenGLPacketPipeline
            pipeline = OpenGLPacketPipeline()

        except Exception as e:
            print(e)
            try:
                from pylibfreenect2 import OpenCLPacketPipeline
                pipeline = OpenCLPacketPipeline()

            except Exception as e:
                print(e)
                from pylibfreenect2 import CpuPacketPipeline
                pipeline = CpuPacketPipeline()
        print("Packet pipeline:", type(pipeline).__name__)

        # Create and set logger
        setGlobalLogger(None)
        self.matrix_transforms = []
        fn = Freenect2()
        num_devices = fn.enumerateDevices()
        if num_devices == 0:
            print("No device connected!")
            # self.close = True

        serial = fn.getDeviceSerialNumber(0)
        self.device = fn.openDevice(serial, pipeline=pipeline)

        # Register listeners
        self.device.setColorFrameListener(self.listener)
        self.device.setIrAndDepthFrameListener(self.listener)

        self.device.start()

        # NOTE: must be called after device.start()
        self.registration = Registration(self.device.getIrCameraParams(),
                                         self.device.getColorCameraParams())

        self.undistorted = Frame(512, 424, 4)
        self.registered = Frame(512, 424, 4)

        # Optinal parameters for registration
        # set True if you need
        need_big_depth = True
        need_color_depth_map = True

        params = cv2.SimpleBlobDetector_Params()
        # Change thresholds
        params.minThreshold = 10  # the graylevel of images
        params.maxThreshold = 200
        params.filterByCircularity = False
        params.filterByConvexity = False
        params.filterByInertia = False
        # params.filterByColor = True
        # params.blobColor = 255

        # Filter by Area
        params.filterByArea = True
        params.minArea = 20
        self.detector = cv2.SimpleBlobDetector_create(params)

        self.big_depth = Frame(1920, 1082, 4) if need_big_depth else None
        self.color_depth_map = np.zeros((424, 512), np.int32).ravel() \
            if need_color_depth_map else None
        while True:

            frames = self.listener.waitForNewFrame()
            color = frames["color"]
            ir = frames["ir"]
            depth = frames["depth"]
            self.registration.apply(color, depth, self.undistorted, self.registered,
                                    bigdepth=self.big_depth,
                                    color_depth_map=self.color_depth_map)
            depth = depth.asarray()

            # cv2.imshow('color', self.registered.asarray(np.uint8))

            if self.first_depth is None:
                self.first_depth = depth.copy()
                np.savetxt('./configure/first_depth.txt', self.first_depth)

            color_depth = self.registered.asarray(np.uint8)

            new_depth = self.first_depth - depth
            self.image_queue.put(color_depth)
            if len(self.configure.mesh_clients) > 0:
                handle_mesh_thread = threading.Thread(target=handle_mesh, args=(self, new_depth.copy()))
                handle_mesh_thread.start()

            if self.configure.reset:
                grid_size_list = configure.grid_size_list
                grid_transforms = configure.grid_transforms
                self.item_width_list = []
                self.item_height_list = []
                self.color_pixel_list = []
                self.new_depth_list = []
                self.color_row_pixel_list = []
                self.row_pixel_list = []
                self.matrix_transforms = []
                for i in range(0, len(configure.clients)):
                    self.item_width_list.append(int(width / grid_size_list[i][0]))
                    self.item_height_list.append(int(height / grid_size_list[i][1]))
                    self.color_pixel_list.append([])
                    self.new_depth_list.append([])
                    self.color_row_pixel_list.append([])
                    self.row_pixel_list.append([])

                for i in range(0, len(configure.clients)):
                    matrix_transform = []
                    grid_transform = grid_transforms[i]
                    for row in range(0, grid_size_list[i][0]):
                        for column in range(0, grid_size_list[i][1]):
                            index1 = column * (grid_size_list[i][0] + 1) + row
                            index2 = column * (grid_size_list[i][0] + 1) + row + 1
                            index3 = (column + 1) * (grid_size_list[i][0] + 1) + row
                            index4 = (column + 1) * (grid_size_list[i][0] + 1) + row + 1

                            m = cv2.getPerspectiveTransform(
                                np.float32(
                                    [(grid_transform[index1][0], grid_transform[index1][1]),
                                     (grid_transform[index2][0], grid_transform[index2][1]),
                                     (grid_transform[index3][0], grid_transform[index3][1]),
                                     (grid_transform[index4][0], grid_transform[index4][1])]),
                                np.float32(
                                    [(0, 0),
                                     (self.item_width_list[i], 0),
                                     (0, self.item_height_list[i]),
                                     (self.item_width_list[i], self.item_height_list[i])]
                                ),
                            )
                            matrix_transform.append(m)
                    self.matrix_transforms.append(matrix_transform)
                    self.configure.reset = False

            if len(self.configure.clients) > 0:
                detect_thread = threading.Thread(target=detect_blob, args=(self, new_depth.copy()))
                detect_thread.start()

            # self.image_queue.put(color_depth)

            self.listener.release(frames)

            key = cv2.waitKey(delay=1)

            if key == ord('q'):
                break

        self.close = True
        self.device.stop()
        self.device.close()


def handle_mesh(self, mesh_depth):
    _, mesh_depth = cv2.threshold(mesh_depth, 90, 255, cv2.THRESH_BINARY)
    for i in range(0, len(self.configure.mesh_clients)):
        mesh_matrix = cv2.getPerspectiveTransform(self.configure.mesh_transforms[i],
                                                  np.float32([[0, 0],
                                                              [512, 0],
                                                              [0, 424],
                                                              [512, 424]]))
        client_mesh_depth = cv2.warpPerspective(mesh_depth, mesh_matrix, (512, 424))
        client_mesh_depth = client_mesh_depth.astype(np.uint8)
        image = cv2.bilateralFilter(client_mesh_depth, 11, 17, 17)
        kernel = np.ones((self.kernel, self.kernel), np.uint8)
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        image = cv2.flip(image, 0)
        contours, hierarchy = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        data = []

        drawing = np.zeros((image.shape[0], image.shape[1], 3), np.uint8)
        for j in range(len(contours)):
            current_area = cv2.contourArea(contours[j])
            if current_area >= self.area:
                epsilon = 0.01 * cv2.arcLength(contours[j], True)
                approx = cv2.approxPolyDP(contours[j], epsilon, True)
                data.append(approx.tolist())
                area = cv2.contourArea(contours[j])
                if (len(approx) > 8) & (area > 30):
                    color_contours = (0, 255, 0)
                    cv2.drawContours(drawing, [approx], -1, color_contours, 1)

        if len(data) > 0:
            self.configure.mesh_queues[i].put(json.dumps(data))


def detect_blob(self, new_depth):
    try:
        for i in range(0, len(self.configure.clients)):
            row_pixel = []
            for row in range(0, self.grid_size_list[i][0]):
                column_pixel = []
                for column in range(0, self.grid_size_list[i][1]):
                    m = self.matrix_transforms[i][row + self.grid_size_list[i][0] * column]
                    m2 = cv2.warpPerspective(new_depth, m, (self.item_width_list[i], self.item_height_list[i]))
                    if column == 0:
                        column_pixel = m2
                    else:
                        column_pixel = np.concatenate((column_pixel, m2), axis=0)
                if row == 0:
                    row_pixel = column_pixel
                else:
                    row_pixel = np.concatenate((row_pixel, column_pixel), axis=1)

            self.row_pixel_list[i] = row_pixel.copy()

            self.new_depth_list[i] = row_pixel.copy()
            subtracted = self.new_depth_list[i]
            _, self.new_depth_list[i] = cv2.threshold(self.new_depth_list[i], 90, 255, cv2.THRESH_BINARY_INV)

            image = self.new_depth_list[i]

            image = image.astype(np.uint8)

            # image = cv2.bilateralFilter(image, 11, 17, 17)

            kernel = np.ones((self.kernel, self.kernel), np.uint8)

            image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

            image = cv2.flip(image, 0)

            # _, image = cv2.threshold(image, 90, 255, cv2.THRESH_BINARY_INV)
            key_points = self.detector.detect(image)
            values = []
            for keypoint in key_points:
                if subtracted[int(keypoint.pt[1])][int(keypoint.pt[0])] <= self.min_depth and\
                        keypoint.size > 10:
                    value = {'y': keypoint.pt[1],
                             'x': self.configure.width - keypoint.pt[0],
                             'size': keypoint.size}
                    values.append(value)
            self.queues[i].put(json.dumps(values))
    except Exception as e:
        print(e)
