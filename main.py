from queue import Queue

from configure import Configure
from kinect_worker import KinectWorker
from udp_server import KinectWebSocket, UdpServer

if __name__ == "__main__":
    configure = Configure()
    queue = Queue()
    kinect_worker = KinectWorker(configure=configure, queue=queue)

    # kinect_server = UdpServer(configure=configure, queue=queue)
    kinect_server = KinectWebSocket(queue=queue)
    kinect_server.start()
    # new_loop = asyncio.new_event_loop()
    # start_server = websockets.serve(kinect_server.handler,  '0.0.0.0', configure.port, loop=new_loop)
    # t = Thread(target=kinect_server.start_loop, args=(new_loop, start_server))
    # t.start()
    # while True:
    #     t = 0
    kinect_worker.run()
    # ws_server = websockets.serve(kinect_server.handler, '0.0.0.0', configure.port)
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(ws_server)
    # loop.run_forever()
