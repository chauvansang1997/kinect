import configparser
import math
import os
from queue import Queue

import numpy as np


class Configure:
    def __init__(self):
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
            top_secret['grid_size_x'] = '1'
            top_secret['grid_size_y'] = '1'
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
            self.grid_size_x = int(self.config['server.com']['grid_size_x'])
            self.grid_size_y = int(self.config['server.com']['grid_size_y'])
            self.config_recv_port = int(self.config['server.com']['config_recv_port'])
            self.config_recv_ip = self.config['server.com']['config_recv_ip']
            self.config_send_port = int(self.config['server.com']['config_send_port'])

            self.config_send_ip = self.config['server.com']['config_send_ip']
            self.config_detect_ip = self.config['server.com']['config_detect_ip']
            self.config_detect_port = int(self.config['server.com']['config_detect_port'])
            self.server_ips = self.config['server.com']['config_detect_port']
            self.grid_size_list_x = self.config['server.com']['grid_size_list_x']
            self.grid_size_list_y = self.config['server.com']['grid_size_list_y']
            self.server_ips = self.server_ips.split(' ')
            self.grid_size_list_x = self.grid_size_list_x.split(' ')
            self.grid_size_list_y = self.grid_size_list_y.split(' ')
            self.ports = self.config['server.com']['ports']
            self.ports = self.ports.split(' ')

        self.width = 512
        self.height = 424
        try:
            self.first_depth = np.loadtxt("first_depth.txt", dtype=np.float32)
            self.transform = np.loadtxt("transform.txt", dtype=np.float32)
            self.grid_transform = np.loadtxt("grid_transform.txt", dtype=np.float32)
            self.grid_transforms = []
            self.queues = []
            for port in self.ports:
                self.queues.append(Queue())
                self.grid_transforms.append(
                    np.loadtxt("grid_transforms_{0}.txt".format(port), dtype=np.float32))
            self.base_grid_transform = np.loadtxt("base_grid_transform.txt", dtype=np.float32)

        except Exception as e:
            print(e)
            self.transform = np.float32([[0, 0], [512, 0], [0, 424], [512, 424]])
            self.wrap_transform = []
            self.grid_transform = []
            self.grid_transforms = []
            self.base_grid_transform = []
            number_point_x = self.grid_size_x + 1
            number_point_y = self.grid_size_y + 1

            for port in self.ports:
                grid_transform = []
                for i in range(0, number_point_x * number_point_y):
                    x = (i % number_point_x) * (self.width / self.grid_size_x)
                    y = math.trunc(math.trunc(i / number_point_x) % number_point_y) * \
                        (self.height / self.grid_size_y)
                    grid_transform.append([x, y])

                np.savetxt("grid_transforms_{0}.txt".format(port), grid_transform)
                self.grid_transforms.append(grid_transform)

            for i in range(0, number_point_x * number_point_y):
                x = (i % number_point_x) * (self.width / self.grid_size_x)
                y = math.trunc(math.trunc(i / number_point_x) % number_point_y) * (self.height / self.grid_size_y)
                self.grid_transform.append([x, y])
                self.base_grid_transform.append([x, y])

            self.grid_transform = np.asarray(self.grid_transform)
            self.base_grid_transform = np.asarray(self.base_grid_transform)

            np.savetxt("transform.txt", self.transform)
            np.savetxt("grid_transform.txt", self.grid_transform)
            np.savetxt("base_grid_transform.txt", self.base_grid_transform)

        self.update = False
        self.update_grid_size = False
        self.update_grid_transform = False
        self.update_wrap_transform = False

    def write(self):
        if os.path.exists('config_kinect.ini') is False:
            self.config['server.com'] = {}
            top_secret = self.config['server.com']
            top_secret['min_depth'] = self.min_depth
            top_secret['server_ip'] = self.server_ip
            top_secret['area'] = self.area
            top_secret['max_depth'] = self.max_depth
            top_secret['kernel'] = self.kernel
            top_secret['port'] = str(self.port)
            top_secret['kinect_id'] = self.kinect_id
            top_secret['config_recv_port'] = str(self.config_recv_port)
            top_secret['config_recv_ip'] = self.config_recv_ip
            top_secret['config_send_port'] = str(self.config_send_port)
            top_secret['config_send_ip'] = self.config_send_ip
            top_secret['server_ip'] = self.server_ip

            with open('config_kinect.ini', 'w') as configfile:
                self.config.write(configfile)

    def write_transform(self, transform):
        self.transform = transform
        np.savetxt("transform.txt", self.transform)
        self.update = True

    def write_wrap_transform(self, transform):
        self.wrap_transform = transform
        np.savetxt("wrap_transform.txt", self.wrap_transform)
        self.update = True

    def write_grid_transform(self, transform):
        self.grid_transform = transform
        np.savetxt("grid_transform.txt", self.grid_transform)
        self.update = True

    def write_grid_transforms(self, index):
        np.savetxt("grid_transforms_{0}.txt".format(index), self.grid_transforms[index])
        self.update = True
