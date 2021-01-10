# coding: utf-8
# from cofigure import Configure
import sys

import cv2
import numpy as np
from pylibfreenect2 import FrameType, Registration, Frame
from pylibfreenect2 import Freenect2, SyncMultiFrameListener
from pylibfreenect2 import LoggerLevel
from pylibfreenect2 import createConsoleLogger, setGlobalLogger

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

while True:
    frames = listener.waitForNewFrame()

    color = frames["color"]
    ir = frames["ir"]
    depth = frames["depth"]

    registration.apply(color, depth, undistorted, registered,
                       bigdepth=bigdepth,
                       color_depth_map=color_depth_map)
    image = depth.asarray()

    cv2.imshow("image", image/4500.0)

    listener.release(frames)

    key = cv2.waitKey(delay=1)
    if key == ord('q'):
        np.savetxt("first_depth.txt", image)
        break

device.stop()
device.close()

sys.exit(0)
