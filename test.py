import math

import cv2
import numpy as np

width = 1200
height = 900
# blank_image = np.zeros((height, width, 3), np.uint8)
blank_image = cv2.imread('test.png')
grid_size_x = 5
grid_size_y = 5

number_point_x = grid_size_x + 1
number_point_y = grid_size_y + 1

transform_points = []
base_transform_points = []

item_width = int(width / grid_size_x)
item_height = int(height / grid_size_y)
for i in range(0, number_point_x * number_point_y):
    x = (i % number_point_x) * (width / grid_size_x)
    y = math.trunc(math.trunc(i / number_point_x) % number_point_y) * (height / grid_size_y)
    transform_points.append({'x': int(x), 'y': int(y)})
    base_transform_points.append({'x': int(x), 'y': int(y)})

current_index = 0
current_position_x = 0
current_position_y = 0


def get_position(index):
    return (index % number_point_x) * (width / grid_size_x), math.trunc(
        math.trunc(index / number_point_x) % number_point_y) * (height / grid_size_y)


while True:
    image = blank_image.copy()

    for i in range(0, number_point_x * number_point_y):
        image = cv2.circle(image, (base_transform_points[i]['x'], base_transform_points[i]['y'],),
                           1, (255, 255, 255), 2)

    for i in range(0, number_point_x * number_point_y):
        image = cv2.circle(image, (transform_points[i]['x'], transform_points[i]['y'],),
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
                    [(transform_points[index1]['x'], transform_points[index1]['y']),
                     (transform_points[index2]['x'], transform_points[index2]['y']),
                     (transform_points[index3]['x'], transform_points[index3]['y']),
                     (transform_points[index4]['x'], transform_points[index4]['y'])]),
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

    cv2.imshow('image', image)

    cv2.imshow('row_pixel', row_pixel)

    key = cv2.waitKey(delay=1)
    if key == ord('='):
        current_position_x += 10
        transform_points[current_index]['x'] = current_position_x
    elif key == ord('-'):
        current_position_x -= 10
        transform_points[current_index]['x'] = current_position_x
    elif key == ord('('):
        current_position_y -= 10
        transform_points[current_index]['y+'] = current_position_x
    elif key == ord(')'):
        current_position_y += 10
        transform_points[current_index]['y'] = current_position_x
    elif key == ord('q'):
        break
    elif key >= ord('A') & key <= ord('z'):
        value = key - ord('A')
        if value < len(transform_points):
            current_index = value
