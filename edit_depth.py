import cv2
import numpy as np
def get_rect(x, y, width, height, angle):
    rect = np.array([(0, 0), (width, 0), (width, height), (0, height), (0, 0)])
    theta = (np.pi / 180.0) * angle
    R = np.array([[np.cos(theta), -np.sin(theta)],
                  [np.sin(theta), np.cos(theta)]])
    offset = np.array([x, y])
    transformed_rect = np.dot(rect, R) + offset
    return transformed_rect


drawing=False # true if mouse is pressed
mode=True


# mouse callback function
def paint_draw(event,former_x,former_y,flags,param):
    global current_former_x,current_former_y,drawing, mode

    if event==cv2.EVENT_LBUTTONDOWN:
        drawing=True
        current_former_x,current_former_y=former_x,former_y
    elif event==cv2.EVENT_MOUSEMOVE:
        if drawing==True:
            if mode==True:
                cv2.line(image,(current_former_x,current_former_y),(former_x,former_y),(255,255,255),5)
                current_former_x = former_x
                current_former_y = former_y
                print(image[former_x,former_y])
    elif event==cv2.EVENT_LBUTTONUP:
        drawing=False
        if mode==True:
            cv2.line(image,(current_former_x,current_former_y),(former_x,former_y),(255,255,255),5)
            current_former_x = former_x
            current_former_y = former_y
    return former_x,former_y
image1 = np.loadtxt("first_depth.txt", dtype = np.float32)
image = image1.copy()
cv2.namedWindow("OpenCV Paint Brush")
cv2.setMouseCallback('OpenCV Paint Brush',paint_draw)
while(1):
    cv2.imshow('OpenCV Paint Brush',image)
    # image[image==255] = 3000
    k=cv2.waitKey(1)& 0xFF
    if k==27: #Escape KEY
        image[image==255] = 3000
        np.savetxt('first_depth_edit1.txt', image)
        break
cv2.destroyAllWindows()