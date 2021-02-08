from queue import Queue

from config_recv_socket import ConfigReceiveSocket
from config_send_socket import ConfigSendSocket
from configure import Configure
from transform_worker import TransformWorker

if __name__ == "__main__":
    configure = Configure()
    queue = Queue()
    config_recv_client = ConfigReceiveSocket(configure=configure)

    config_send_client = ConfigSendSocket(configure=configure, queue=queue)
    transform_worker = TransformWorker(configure=configure, queue=queue)
    config_recv_client.start()
    config_send_client.start()
    transform_worker.run()
