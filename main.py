from queue import Queue

from configure import Configure
from kinect_worker import KinectWorker
from udp_client import KinectWebSocket

if __name__ == "__main__":
    configure = Configure()
    queue = Queue()
    kinect_worker = KinectWorker(configure=configure, queue=queue)
    kinect_server = KinectWebSocket(queue=queue, configure=configure)
    kinect_server.start()
    kinect_worker.run()
