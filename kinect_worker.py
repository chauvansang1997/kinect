import json

import cv2
import numpy as np
from pylibfreenect2 import Freenect2, SyncMultiFrameListener, FrameType, Registration, Frame
from pylibfreenect2 import LoggerLevel
from pylibfreenect2 import createConsoleLogger, setGlobalLogger


class KinectWorker:
    def __init__(self, configure, queue):
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
        self.transform = configure.transform
        self.top_left = [0, 0]
        self.top_right = [512, 0]
        self.bottom_left = [0, 424]
        self.bottom_right = [512, 424]

    def run(self):

        configure = self.configure

        def change_min_depth(x):
            configure.config['server.com']['min_depth'] = str(x)
            with open('config_kinect.ini', 'w') as configfile:
                configure.config.write(configfile)

        def change_max_depth(x):
            configure.config['server.com']['max_depth'] = str(x)
            with open('config_kinect.ini', 'w') as configfile:
                configure.config.write(configfile)

        def change_kernel(x):
            configure.config['server.com']['kernel'] = str(x)
            with open('config_kinect.ini', 'w') as configfile:
                configure.config.write(configfile)

        def change_area(x):
            configure.config['server.com']['area'] = str(x)
            with open('config_kinect.ini', 'w') as configfile:
                configure.config.write(configfile)

        def change_warp_points(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONUP:
                self.transform[self.index] = [x, y]
                print([x, y])
                np.savetxt("transform.txt", self.transform)
                self.index = self.index + 1
                self.index = self.index % 4

        cv2.namedWindow('track')
        cv2.namedWindow('color')
        cv2.setMouseCallback('color', change_warp_points)
        cv2.createTrackbar('min_depth', 'track', 0, 4500, change_min_depth)
        cv2.createTrackbar('area', 'track', 0, 4500, change_area)
        cv2.createTrackbar('max_depth', 'track', 0, 4500, change_max_depth)
        cv2.createTrackbar('kernel', 'track', 0, 15, change_kernel)

        cv2.setTrackbarPos('min_depth', 'track', self.min_depth)
        cv2.setTrackbarPos('max_depth', 'track', self.max_depth)
        cv2.setTrackbarPos('kernel', 'track', self.kernel)
        cv2.setTrackbarPos('area', 'track', self.area)
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

            new_depth = self.first_depth - depth

            M = cv2.getPerspectiveTransform(self.transform,
                                            np.float32([[0, 0],
                                                        [512, 0],
                                                        [0, 424],
                                                        [512, 424]]))

            new_depth = cv2.warpPerspective(new_depth, M, (512, 424))
            color_depth = cv2.warpPerspective(self.registered.asarray(np.uint8), M, (512, 424))
            subtracted = new_depth
            _, new_depth = cv2.threshold(new_depth, 90, 255, cv2.THRESH_BINARY)
            cv2.imshow('current depth', depth / 4500.)

            cv2.imshow("subtracted depth", new_depth)
            cv2.imshow("color depth", color_depth)

            image = new_depth

            image = image.astype(np.uint8)

            image = cv2.bilateralFilter(image, 11, 17, 17)

            kernel = np.ones((self.kernel, self.kernel), np.uint8)

            image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

            image = cv2.flip(image, 0)
            _, image = cv2.threshold(image, 90, 255, cv2.THRESH_BINARY_INV)
            key_points = detector.detect(image)

            values = []
            # self.queue.put('test')
            for keypoint in key_points:
                if subtracted[int(keypoint.pt[1])][int(keypoint.pt[0])] <= self.min_depth:
                    value = {'y': keypoint.pt[1],
                             'x': keypoint.pt[0],
                             'size': keypoint.size}
                    values.append(value)
                # value = {'y': keypoint.pt[1],
                #          'x': keypoint.pt[0],
                #          'size': keypoint.size}
                # values.append(value)
                print(subtracted[int(keypoint.pt[1])][int(keypoint.pt[0])])
            if len(key_points) != 0:
                self.queue.put(json.dumps(values))

            im_with_key_points = cv2.drawKeypoints(image, key_points, np.array([]),
                                                   (0, 255, 0),
                                                   cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

            cv2.imshow("key_points", im_with_key_points)

            cv2.imshow("image", image)

            self.listener.release(frames)

            key = cv2.waitKey(delay=1)
            if key == ord('k'):
                np.savetxt('subtracted.txt', image)
            if key == ord('q'):
                break

        self.close = True
        self.device.stop()
        self.device.close()
