import math

import cv2
import numpy as np


class TransformWorker:
    def __init__(self, configure, queue):
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

    def run(self):
        configure = self.configure
        width = configure.width
        height = configure.height

        grid_size_x = configure.grid_size_x
        grid_size_y = configure.grid_size_y
        number_point_x = configure.grid_size_x + 1
        number_point_y = configure.grid_size_y + 1
        current_index = 0
        current_position_x = 0
        current_position_y = 0
        blank_image = cv2.imread('test.png')
        blank_image = cv2.resize(blank_image, (width, height), interpolation=cv2.INTER_AREA)
        grid_transform = configure.grid_transform
        base_grid_transform = configure.base_grid_transform

        item_width = int(width / grid_size_x)
        item_height = int(height / grid_size_y)
        while True:
            image = blank_image.copy()
            if self.configure.update:
                self.configure.update = False
                grid_transform = self.configure.grid_transform

            for i in range(0, number_point_x * number_point_y):
                image = cv2.circle(image, (base_grid_transform[i][0], base_grid_transform[i][1],),
                                   1, (255, 255, 255), 2)

            for i in range(0, number_point_x * number_point_y):
                image = cv2.circle(image, (grid_transform[i][0], grid_transform[i][1],),
                                   1, (255, 0, 255), 2)

            row_pixel = []
            for row in range(0, grid_size_x):
                column_pixel = []
                for column in range(0, grid_size_y):
                    index1 = column * number_point_x + row
                    index2 = column * number_point_x + row + 1
                    index3 = (column + 1) * number_point_x + row
                    index4 = (column + 1) * number_point_x + row + 1

                    m2 = cv2.getPerspectiveTransform(
                        np.float32(
                            [(grid_transform[index1][0], grid_transform[index1][1]),
                             (grid_transform[index2][0], grid_transform[index2][1]),
                             (grid_transform[index3][0], grid_transform[index3][1]),
                             (grid_transform[index4][0], grid_transform[index4][1])]),
                        np.float32(
                            [(0, 0),
                             (item_width, 0),
                             (0, item_height),
                             (item_width, item_height)]
                        ),
                    )
                    m2 = cv2.warpPerspective(image, m2, (item_width, item_height))

                    if column == 0:
                        column_pixel = m2
                    else:
                        column_pixel = np.concatenate((column_pixel, m2), axis=0)

                if row == 0:
                    row_pixel = column_pixel
                else:
                    row_pixel = np.concatenate((row_pixel, column_pixel), axis=1)

            self.queue.put(image)

            # cv2.imshow('image', image)
            cv2.imshow('row_pixel_client', row_pixel)

            key = cv2.waitKey(delay=1)
            if key == ord('q'):
                break
