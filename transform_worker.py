import cv2
import numpy as np


class TransformWorker:
    def __init__(self, configure, image_queue):
        self.available_data = False
        self.close = False
        self.configure = configure
        self.min_depth = int(configure.min_depth)
        self.max_depth = int(configure.max_depth)
        self.kernel = int(configure.kernel)
        self.kinect_id = configure.kinect_id
        self.first_depth = configure.first_depth
        self.area = int(configure.area)
        self.queues = configure.queues
        self.image_queue = image_queue
        self.transform = configure.transform

    def run(self):
        configure = self.configure
        width = configure.width
        height = configure.height

        grid_size_list_x = configure.grid_size_list_x
        grid_size_list_y = configure.grid_size_list_y
        grid_transforms = configure.grid_transforms
        number_point_list_x = []
        number_point_list_y = []
        item_width_list = []
        item_height_list = []

        for i in range(0, len(grid_size_list_x)):
            number_point_list_x.append(grid_size_list_x[i] + 1)
            number_point_list_y.append(grid_size_list_y[i] + 1)
            item_width_list.append(int(width / grid_size_list_x[i]))
            item_height_list.append(int(height / grid_size_list_y[i]))

        blank_image = cv2.imread('test.png')
        blank_image = cv2.resize(blank_image, (width, height), interpolation=cv2.INTER_AREA)

        while True:
            image = blank_image.copy()
            if self.configure.update:
                self.configure.update = False
                grid_transforms = self.configure.grid_transforms
            self.image_queue.put(image)
            for i in range(0, configure.server_ips):
                row_pixel = []
                color_row_pixel = []
                grid_transform = grid_transforms[i]
                for row in range(0, grid_size_list_x[i]):
                    column_pixel = []
                    for column in range(0, grid_size_list_y[i]):
                        index1 = column * number_point_list_x[i] + row
                        index2 = column * number_point_list_x[i] + row + 1
                        index3 = (column + 1) * number_point_list_x[i] + row
                        index4 = (column + 1) * number_point_list_x[i] + row + 1

                        m = cv2.getPerspectiveTransform(
                            np.float32(
                                [(grid_transform[index1][0], grid_transform[index1][1]),
                                 (grid_transform[index2][0], grid_transform[index2][1]),
                                 (grid_transform[index3][0], grid_transform[index3][1]),
                                 (grid_transform[index4][0], grid_transform[index4][1])]),
                            np.float32(
                                [(0, 0),
                                 (item_width_list[i], 0),
                                 (0, item_height_list[i]),
                                 (item_width_list[i], item_height_list[i])]
                            ),
                        )
                        m2 = cv2.warpPerspective(image, m, (item_width_list[i], item_height_list[i]))
                        if column == 0:
                            column_pixel = m2
                        else:
                            column_pixel = np.concatenate((column_pixel, m2), axis=0)

                    if row == 0:
                        row_pixel = column_pixel
                    else:
                        row_pixel = np.concatenate((row_pixel, column_pixel), axis=1)

                cv2.imshow('color_row_pixel'.format(i), color_row_pixel)

                cv2.imshow('row_pixel_client_{0}'.format(i), row_pixel)

            key = cv2.waitKey(delay=1)
            if key == ord('q'):
                break
