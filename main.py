from queue import Queue

from config_detect_socket import ConfigDetectSocket
from config_recv_socket import ConfigReceiveSocket
from config_send_socket import ConfigSendSocket
from configure import Configure
from kinect_worker import KinectWorker
from udp_client import KinectWebSocket

if __name__ == "__main__":
    configure = Configure()
    image_queue = Queue()
    detect_queue = Queue()
    for i in range(0, configure.server_ips):
        kinect_server = KinectWebSocket(index=i, configure=configure)
        kinect_server.start()

    config_recv_client = ConfigReceiveSocket(configure=configure)
    config_send_client = ConfigSendSocket(configure=configure, queue=image_queue)
    config_detect_client = ConfigDetectSocket(configure=configure, queue=detect_queue)
    config_recv_client.start()
    config_send_client.start()
    config_detect_client.start()

    kinect_worker = KinectWorker(configure=configure, image_queue=image_queue, detect_queue=detect_queue)
    kinect_worker.run()
