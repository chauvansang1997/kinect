import cv2
import numpy as np

image = np.loadtxt("subtracted.txt", dtype = np.float32)
params = cv2.SimpleBlobDetector_Params()
# Change thresholds
params.minThreshold = 10  # the graylevel of images
params.maxThreshold = 200
params.filterByCircularity = False
params.filterByConvexity = False
params.filterByInertia = False
# params.filterByColor = True
# params.blobColor = 255

# Filter by Area
params.filterByArea = True
params.minArea = 20
detector = cv2.SimpleBlobDetector_create(params)
image = image.astype(np.uint8)
while True:

    keypoints = detector.detect(image)

    # _, image = cv2.threshold(image, 90, 255, cv2.THRESH_BINARY_INV)
    im_with_keypoints = cv2.drawKeypoints(image, keypoints, np.array([]),
                                          (0, 255, 0),
                                          cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    cv2.imshow("Keypoints", im_with_keypoints)

    cv2.imshow("subtracted",image)
    key = cv2.waitKey(delay=1)
    if key == ord('q'):
        break