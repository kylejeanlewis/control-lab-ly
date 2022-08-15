# %%
# -*- coding: utf-8 -*-
"""
Created on Fri 2022/03/18 09:00:00

@author: Chang Jie
"""
import os
import cv2
from thermal.ax8.ax8 import Ax8ThermalCamera
from image_recognition import Vision
print(f"Import: OK <{__name__}>")

here = os.getcwd()
base = here.split('src')[0] + 'src'
DEMO_IRC_PATH = f"{base}\\utils\\image\\demo\\demo_irc.png"

# %% Thermal
class Thermal(Ax8ThermalCamera):
    def __init__(self, ip_address: str, encoding: str = "avc", overlay: bool = False, verbose: bool = True, cam_size=(640,480)):
        try:
            super().__init__(ip_address, encoding, overlay, verbose)
        except:
            pass
        self.cam_size = cam_size
        return

    def read_image(self, crosshair=True):
        """
        Retreive image from camera capture
        - crosshair: whether to display crosshair on image

        Return: bool, image
        """
        ret = False
        try:
            frame = self.video.stream.read()
            frame = self.rotate180(frame)
            ret = True
        except:
            frame = cv2.imread(DEMO_IRC_PATH)
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

    def rotate180(self, frame):
        """
        Rotate the frame by 180 degrees
        - frame: image

        Return: rotated image
        """
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        return frame

