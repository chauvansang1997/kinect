# coding: utf-8
# from cofigure import Configure
import configparser
import os
import sys

import cv2
import numpy as np
from pylibfreenect2 import FrameType, Registration, Frame
from pylibfreenect2 import Freenect2, SyncMultiFrameListener
from pylibfreenect2 import LoggerLevel
from pylibfreenect2 import createConsoleLogger, setGlobalLogger

from client import Client

config = configparser.ConfigParser()
minDepth = 0
maxDepth = 200
minHeight = 20
maxHeight = 40
minWidth = 20
maxWidth = 40
threshHold = 200
kernel = 2
host = 'https://192.168.0.100'
port = 8080
kinect_id = 1
if os.path.exists('config_kinect.ini') is False:
    config['server.com'] = {}
    top_secret = config['server.com']
    top_secret['minDepth'] = minDepth
    top_secret['maxDepth'] = maxDepth
    top_secret['minHeight'] = minHeight
    top_secret['maxHeight'] = maxHeight
    top_secret['minWidth'] = minWidth
    top_secret['maxWidth'] = maxWidth
    top_secret['threshHold'] = threshHold
    top_secret['kernel'] = kernel
    top_secret['host'] = host
    top_secret['port'] = port
    top_secret['kinect_id'] = kinect_id
    with open('config_kinect.ini', 'w') as configfile:
        config.write(configfile)
else:
    config.read('config_kinect.ini')
    minDepth = config['server.com']['minDepth']
    maxDepth = config['server.com']['maxDepth']
    minHeight = config['server.com']['minHeight']
    maxHeight = config['server.com']['maxHeight']
    minWidth = config['server.com']['minWidth']
    maxWidth = config['server.com']['maxWidth']
    threshHold = config['server.com']['threshHold']
    kernel = config['server.com']['kernel']
    host = config['server.com']['host']
    port = config['server.com']['port']
    kinect_id = config['server.com']['kinect_id']


def change_threshold(x):
    config['server.com']['threshHold'] = str(x)
    with open('config_kinect.ini', 'w') as configfile:
        config.write(configfile)


def change_minWidth(x):
    config['server.com']['minWidth'] = str(x)
    with open('config_kinect.ini', 'w') as configfile:
        config.write(configfile)


def change_maxWidth(x):
    config['server.com']['maxWidth'] = str(x)
    with open('config_kinect.ini', 'w') as configfile:
        config.write(configfile)


def change_minHeight(x):
    config['server.com']['minHeight'] = str(x)
    with open('config_kinect.ini', 'w') as configfile:
        config.write(configfile)


def change_maxHeight(x):
    config['server.com']['maxHeight'] = str(x)
    with open('config_kinect.ini', 'w') as configfile:
        config.write(configfile)


def change_kernel(x):
    config['server.com']['kernel'] = str(x)
    with open('config_kinect.ini', 'w') as configfile:
        config.write(configfile)


def nothing(x):
    pass


cv2.namedWindow('track')
cv2.createTrackbar('minHeight', 'track', 0, 4500, change_minHeight)
cv2.createTrackbar('maxHeight', 'track', 0, 4500, change_maxHeight)
cv2.createTrackbar('kernel', 'track', 0, 15, change_kernel)

cv2.setTrackbarPos('minHeight', 'track', int(minHeight))
cv2.setTrackbarPos('maxHeight', 'track', int(maxHeight))
cv2.setTrackbarPos('kernel', 'track', int(kernel))

# create switch for ON/OFF functionality
switch = '0 : OFF \n1 : ON'
cv2.createTrackbar(switch, 'track', 0, 1, nothing)

height_rect = 200
width_rect = 200
list_rect = []
list_contour = []
temp_contour = []
blank_image = np.zeros((500, 500, 3), np.uint8)
while True:
    max_width = cv2.getTrackbarPos('maxWidth', 'track')
    max_height = cv2.getTrackbarPos('maxHeight', 'track')
    kernel = cv2.getTrackbarPos('kernel', 'track')

    cv2.imshow('track', blank_image)
    key = cv2.waitKey(delay=1)
    if key == ord('q'):
        break

client = Client(url=host, port=port, kinect_id=kinect_id)
try:
    from pylibfreenect2 import OpenGLPacketPipeline

    pipeline = OpenGLPacketPipeline()
except:
    try:
        from pylibfreenect2 import OpenCLPacketPipeline

        pipeline = OpenCLPacketPipeline()
    except:
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
    sys.exit(1)

serial = fn.getDeviceSerialNumber(0)
device = fn.openDevice(serial, pipeline=pipeline)

listener = SyncMultiFrameListener(
    FrameType.Color | FrameType.Ir | FrameType.Depth)

# Register listeners
device.setColorFrameListener(listener)
device.setIrAndDepthFrameListener(listener)

device.start()

# NOTE: must be called after device.start()
registration = Registration(device.getIrCameraParams(),
                            device.getColorCameraParams())

undistorted = Frame(512, 424, 4)
registered = Frame(512, 424, 4)

# Optinal parameters for registration
# set True if you need
need_bigdepth = True
need_color_depth_map = True

bigdepth = Frame(1920, 1082, 4) if need_bigdepth else None
color_depth_map = np.zeros((424, 512), np.int32).ravel() \
    if need_color_depth_map else None
# listener.release(frames)
while True:
    list_rect.clear()
    list_contour.clear()
    frames = listener.waitForNewFrame()

    color = frames["color"]
    ir = frames["ir"]
    depth = frames["depth"]

    registration.apply(color, depth, undistorted, registered,
                       bigdepth=bigdepth,
                       color_depth_map=color_depth_map)
    threshHold = cv2.getTrackbarPos('threshHold', 'track')
    min_width = cv2.getTrackbarPos('minWidth', 'track')
    min_height = cv2.getTrackbarPos('minHeight', 'track')
    max_width = cv2.getTrackbarPos('maxWidth', 'track')
    max_height = cv2.getTrackbarPos('maxHeight', 'track')
    kernel = cv2.getTrackbarPos('kernel', 'track')

    image = depth.asarray()

    cv2.imshow("color", registered.asarray())

    image[np.logical_or((image < min_height), (image > max_height))] = 0
    image[(image >= min_height * (image <= max_height))] = 4500
    image = image / 4500.

    image = (image * 255).astype(np.uint8)

    im2, contours, hierarchy = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # create hull array for convex hull points
    hull = []
    # calculate points for each contour
    for i in range(len(contours)):
        # creating convex hull object for each contour
        hull.append(cv2.convexHull(contours[i], False))
        print(cv2.convexHull(contours[i], False))

    result = hull[0]

    for i in range(len(hull)):
        if len(result) < len(hull[i]):
            result = hull[i]

    client.send_points(result)

    image = cv2.bilateralFilter(image, 11, 17, 17)
    kernel = np.ones((kernel, kernel), np.uint8)
    image = cv2.dilate(image, kernel, iterations=1)
    # image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
    # image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    edged = cv2.Canny(image, 30, 200)
    # color_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    # create an empty black image
    drawing = np.zeros((image.shape[0], image.shape[1], 3), np.uint8)
    for i in range(len(contours)):
        color_contours = (0, 255, 0)
        color = (255, 0, 0)  # blue - color for convex hull
        cv2.drawContours(drawing, contours, i, color_contours, 1, 8, hierarchy)
        cv2.drawContours(drawing, hull, i, color, 1, 8)

    cv2.imshow("track", drawing)

    listener.release(frames)

    key = cv2.waitKey(delay=1)
    if key == ord('q'):
        break

device.stop()
device.close()

sys.exit(0)
