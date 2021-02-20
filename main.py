from queue import Queue

from client_kinect import ClientKinectSocket
from config_recv_socket import ConfigReceiveSocket
from configure import Configure
from frame_segment_udp import FrameSegment
from kinect_worker import KinectWorker

if __name__ == "__main__":
    configure = Configure()
    image_queue = Queue()
    detect_queue = Queue()

    config_recv_client = ConfigReceiveSocket(configure=configure)
    clientKinectSocket = ClientKinectSocket(configure=configure)
    frameSegment = FrameSegment(configure=configure, image_queue=image_queue)
    clientKinectSocket.start()
    frameSegment.start()
    config_recv_client.start()

    kinect_worker = KinectWorker(configure=configure, image_queue=image_queue, detect_queue=detect_queue)
    kinect_worker.run()
