# %%
# -*- coding: utf-8 -*-
"""
Created on Fri 2022/03/18 09:00:00

@author: Chang Jie
"""
import os
import numpy as np
import pandas as pd
import cv2 # pip install opencv-python
print(f"Import: OK <{__name__}>")

here = os.getcwd()
base = here.split('src')[0] + 'src'
DEMO_CAM_PATH = f"{base}\\utils\\image\\demo\\demo_cam.png"

# %% Computer Vision
class Vision(object):
    """
    Computer vision methods.
    - calib_unit: image-to-physical unit conversion
    - cam_size: (W, H) of camera output
    """
    def __init__(self, calib_unit, cam_size=(640,480)):
        self.cam_size = cam_size
        self.calib_unit = calib_unit
        self.cascade = None
        self.cap = None
        try:
            self.cap = cv2.VideoCapture(0)
            pass
        except:
            pass
        return

    def annotate(self, df, frame, opening_iter=0, closing_iter=0):
        """
        Annotate the image to label identified targets
        - df: dataframe of identified targets
        - frame: image
        - opening_iter: BG noise removal iterations
        - closing_iter: FG noise removal iterations

        Return: image
        """
        data = {}
        for i in range(len(df)):
            x = df.loc[i,'x']
            y = df.loc[i,'y']
            w = df.loc[i,'w']
            h = df.loc[i,'h']
            area = w*h
            if area >= 36*36:
                data['C'+str(i+1)] = [int(x+(w/2)), int(y+(h/2))]

                cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
                cv2.circle(frame, (int(x+(w/2)), int(y+(h/2))), 3, (0,0,255), -1)
                cv2.putText(frame, '{}'.format(i+1), (x-8, y-4), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.6, (255,255,255), 1)
                roi_color = frame[y:y+h, x:x+w]
                roi_gray = cv2.cvtColor(roi_color, cv2.COLOR_BGR2GRAY)

                # Morphological Transformations - Noise Removal
                kernel = np.ones((3,3),np.uint8)
                roi_gray = cv2.morphologyEx(roi_gray,cv2.MORPH_OPEN,kernel,iterations=opening_iter)
                roi_gray = cv2.morphologyEx(roi_gray,cv2.MORPH_CLOSE,kernel,iterations=closing_iter)

                # Image Thresholding: Inverse Binary Thresholding + the OTSU method
                ret, thresh = cv2.threshold(roi_gray, 127, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
                
                # Contour Detection
                # contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
                # contours = contours[1:]
                # cv2.drawContours(roi_color, contours, -1, (255,0,0), 2)
        return data, frame

    def annotate_one(self, row, frame, color_bgr):
        """
        Annotate the image to label one target
        - row: dataframe row of identified targets
        - frame: image
        - color_bgr: color of rectangle to be drawn

        Return: image
        """
        x,y,w,h = row.to_list()[:4]
        cv2.rectangle(frame, (x,y), (x+w, y+h), color_bgr, 2)
        return frame

    def capture_image(self, frame, imgpath):
        """
        Save frame as image file
        - frame: image
        - imgpath: filepath to write image to

        Return: int, int (center coordinates of image)
        """
        cv2.imwrite(imgpath, frame)
        center_x = int(frame.shape[1] / 2)
        center_y = int(frame.shape[0] / 2)
        return center_x, center_y
    
    def checkEscapeKey(self):
        """
        Check if 'Esc' key is pressed
        Return: bool
        """
        return (cv2.waitKey(5) & 0xFF == 27)
    
    def close(self):
        """
        Close camera feed
        """
        self.cap.release()
        cv2.destroyAllWindows()
        return

    def data_to_df(self, data):
        """
        Convert data (dict) to DataFrame
        - data: dict of position data

        Return: pd.DataFrame
        """
        df = pd.DataFrame(data)
        df.rename(columns={0: 'x', 1: 'y', 2: 'w', 3: 'h'}, inplace=True)
        df.sort_values(by='y', ascending=True, inplace=True)
        df.reset_index(inplace=True, drop=True)
        df['row'] = np.ones(len(df), dtype='int64')
        row_num = 1
        for i in np.arange(1,len(df)): 
            # If diff in y-coordinates > 30, assign next row (adjustable)
            if (abs(df.loc[i,'y'] - df.loc[i-1,'y']) > 30):             
                row_num += 1
                df.loc[i,'row'] = row_num
            else:
                df.loc[i,'row'] = row_num
        df.sort_values(by=['row','x'], ascending=[True,True], inplace=True) 
        df.reset_index(inplace = True, drop = True)
        return df

    def detect(self, frame, scale_factor, neighbors):
        """
        Detect the target shape from image
        - frame: image
        - scale_factor: scale factor
        - neighbors: minimum number of neighbors

        Return: pd.Dataframe
        """
        df = pd.DataFrame()
        try:
            gray_img = self.grayscale(frame)
            object_detect = self.cascade.detectMultiScale(image=gray_img, scaleFactor=scale_factor, minNeighbors=neighbors)
            df = self.data_to_df(object_detect)
        except:
            pass
        return df

    def encode(self, frame):
        """
        Encode frame into bytes
        - frame: image

        Return: bytes
        """
        return cv2.imencode('.png', frame)[1].tobytes()

    def getClassifier(self, xml_path):
        """
        Get the Cascade Classifier object
        - xml_path: path of trained .xml data

        Returns: cv2.CascadeClassifier object
        """
        clf = None
        try:
            clf = cv2.CascadeClassifier(xml_path)
        except:
            pass
        return clf

    def grayscale(self, frame):
        """
        Convert image from RGB to grayscale
        - frame: image

        Returns: image
        """
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    def load(self, imgpath):
        """
        Read image from file
        - imgpath: path to image file

        Returns: image
        """
        return cv2.imread(imgpath)

    def process(self, frame, alpha, beta, blur_kernel):
        """
        Process the image for brightness, contrast, and blur
        - frame: image
        - alpha: contrast correction factor
        - beta: brightness correction factor
        - blur_kernel: kernel size

        Return: image
        """
        frame = cv2.addWeighted(frame, alpha, np.zeros(frame.shape, frame.dtype), 0, beta)
        if blur_kernel > 0:
            frame = frame = cv2.GaussianBlur(frame,(blur_kernel,blur_kernel),0)
        return frame
    
    def read_image(self, crosshair=True):
        """
        Retreive image from camera capture
        - crosshair: whether to display crosshair on image

        Return: bool, image
        """
        ret = False
        try:
            ret, frame = self.cap.read()
            if not ret:
                frame = self.load(DEMO_CAM_PATH)
                ret = True
        except:
            frame = self.load(DEMO_CAM_PATH)
            ret = True
        if ret:
            frame = cv2.resize(frame, self.cam_size)

            # Create crosshair in center of image
            if crosshair:
                center_x = int(frame.shape[1] / 2)
                center_y = int(frame.shape[0] / 2)
                cv2.line(frame, (center_x, center_y+50), (center_x, center_y-50), (255,255,255), 1)
                cv2.line(frame, (center_x+50, center_y), (center_x-50, center_y), (255,255,255), 1)
        return ret, frame

    def resize(self, frame, size):
        """
        Resize frame
        - frame: image from camera capture
        - size: (W, H) width and height of image

        Return: image
        """
        return cv2.resize(frame, size)

