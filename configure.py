import configparser
import os

import numpy as np


class Configure:
    def __init__(self):
        try:
            self.transform = np.loadtxt("transform.txt", dtype=np.float32)
            self.first_depth = np.loadtxt("first_depth.txt", dtype=np.float32)
        except Exception as e:
            print(e)
            self.transform = np.float32([[0, 0], [512, 0], [0, 424], [512, 424]])
            self.first_depth = None
            np.savetxt("transform.txt", self.transform)
        self.config = configparser.ConfigParser()
        if os.path.exists('config_kinect.ini') is False:
            self.config['server.com'] = {}
            top_secret = self.config['server.com']
            top_secret['min_depth'] = self.min_depth
            top_secret['server_ip'] = "127.0.0.1"
            top_secret['area'] = '30'
            top_secret['max_depth'] = '0'
            top_secret['kernel'] = '0'
            top_secret['kinect_id'] = '0'
            top_secret['port'] = '8080'
            top_secret['kinect_id'] = '0'
            with open('config_kinect.ini', 'w') as configfile:
                self.config.write(configfile)
        else:
            self.config.read('config_kinect.ini')
            self.min_depth = self.config['server.com']['min_depth']
            self.server_ip = self.config['server.com']['server_ip']
            self.area = self.config['server.com']['area']
            self.max_depth = self.config['server.com']['max_depth']
            self.kernel = self.config['server.com']['kernel']
            self.kinect_id = self.config['server.com']['kinect_id']
            self.port = int(self.config['server.com']['port'])
            self.kinect_id = self.config['server.com']['kinect_id']
