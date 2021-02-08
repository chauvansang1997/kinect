import json

import cv2
import numpy as np
from pylibfreenect2 import Freenect2, SyncMultiFrameListener, FrameType, Registration, Frame
from pylibfreenect2 import LoggerLevel
from pylibfreenect2 import createConsoleLogger, setGlobalLogger


class TransformWorker:
    def __init__(self, configure, queue, image_queue, detect_queue):
        self.listener = SyncMultiFrameListener(
            FrameType.Color | FrameType.Ir | FrameType.Depth)
        self.available_data = False
        self.close = False
        self.configure = configure
        self.min_depth = int(configure.min_depth)
        self.max_depth = int(configure.max_depth)
        self.kernel = int(configure.kernel)
        self.kinect_id = configure.kinect_id
        self.first_depth = configure.first_depth
        self.area = int(configure.area)

        self.index = 0
        self.queue = queue
        self.detect_queue = detect_queue
        self.image_queue = image_queue
        self.transform = configure.transform

    def run(self):
        configure = self.configure
        width = configure.width
        height = configure.height

        grid_size_x = configure.grid_size_x
        grid_size_y = configure.grid_size_y
        number_point_x = configure.grid_size_x + 1
        number_point_y = configure.grid_size_y + 1
        current_index = 0
        current_position_x = 0
        current_position_y = 0
        grid_transform = configure.grid_transform
        base_grid_transform = configure.base_grid_transform

        item_width = int(width / grid_size_x)
        item_height = int(height / grid_size_y)
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
        logger = createConsoleLogger(LoggerLevel.Debug)
        setGlobalLogger(logger)

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
        detector = cv2.SimpleBlobDetector_create(params)

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

            cv2.imshow('color', self.registered.asarray(np.uint8))

            if self.first_depth is None:
                self.first_depth = depth.copy()
                np.savetxt('first_depth.txt', self.first_depth)

            color_depth = self.registered.asarray(np.uint8)
            new_depth = self.first_depth - depth

            if self.configure.update:
                self.configure.update = False
                grid_transform = self.configure.grid_transform

            self.image_queue.put(color_depth)

            row_pixel = []
            color_row_pixel = []
            for row in range(0, grid_size_x):
                column_pixel = []
                color_column_pixel = []
                for column in range(0, grid_size_y):
                    index1 = column * number_point_x + row
                    index2 = column * number_point_x + row + 1
                    index3 = (column + 1) * number_point_x + row
                    index4 = (column + 1) * number_point_x + row + 1

                    m = cv2.getPerspectiveTransform(
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
                    m2 = cv2.warpPerspective(new_depth, m, (item_width, item_height))
                    m1 = cv2.warpPerspective(color_depth, m, (item_width, item_height))
                    if column == 0:
                        column_pixel = m2
                        color_column_pixel = m1
                    else:
                        column_pixel = np.concatenate((column_pixel, m2), axis=0)
                        color_column_pixel = np.concatenate((color_column_pixel, m1), axis=0)

                if row == 0:
                    row_pixel = column_pixel
                    color_row_pixel = color_column_pixel
                else:
                    row_pixel = np.concatenate((row_pixel, column_pixel), axis=1)
                    color_row_pixel = np.concatenate((color_row_pixel, color_column_pixel), axis=1)

            new_depth = row_pixel
            subtracted = new_depth
            cv2.imshow('color_row_pixel', color_row_pixel)

            _, new_depth = cv2.threshold(new_depth, 90, 255, cv2.THRESH_BINARY)

            image = new_depth

            image = image.astype(np.uint8)

            image = cv2.bilateralFilter(image, 11, 17, 17)

            kernel = np.ones((self.kernel, self.kernel), np.uint8)

            image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

            image = cv2.flip(image, 0)

            _, image = cv2.threshold(image, 90, 255, cv2.THRESH_BINARY_INV)

            key_points = detector.detect(image)
            values = []

            for keypoint in key_points:
                if subtracted[int(keypoint.pt[1])][int(keypoint.pt[0])] <= self.min_depth:
                    value = {'y': keypoint.pt[1],
                             'x': self.configure.height - keypoint.pt[0],
                             'size': keypoint.size}
                    values.append(value)

                print(subtracted[int(keypoint.pt[1])][int(keypoint.pt[0])])
            if len(key_points) != 0:
                self.queue.put(json.dumps(values))

            im_with_key_points = cv2.drawKeypoints(image, key_points, np.array([]),
                                                   (0, 255, 0),
                                                   cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

            cv2.imshow("key_points", im_with_key_points)
            self.detect_queue.put(im_with_key_points)

            self.listener.release(frames)

            key = cv2.waitKey(delay=1)
            # if key == ord('k'):
            #     np.savetxt('subtracted.txt', image)
            if key == ord('q'):
                break

        self.close = True
        self.device.stop()
        self.device.close()