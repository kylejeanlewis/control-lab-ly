# -*- coding: utf-8 -*-
"""
Class to work with the AX8 thermal camera feed 

Created on Tue Aug 17 11:11:50 2021

@author: Sharath
"""
import cv2 # pip install opencv-python
from imutils.video import VideoStream # pip install imutils
import threading

class Ax8CameraFeed:
    def __init__(self, ip_address:str, encoding:str = 'avc', overlay:bool = False):
        # Set up the RTSP feed
        self.rtsp_url = self.get_rtsp_url(ip_address, encoding, overlay)
        print("Opening camera feed at " + self.rtsp_url)
        self.stream = VideoStream(self.rtsp_url).start()
        # Ensure stream is working correctly
        if self.stream.frame is None:
            self.stream.stop() # Probably unnecessary since it is a daemon
            raise AttributeError("Could not open stream at {}!".format(self.rtsp_url))
        # Stream is good
        self.viewer = CameraViewer(self.stream)
        
    def get_rtsp_url(self, ip_address, encoding, overlay):
        out = "rtsp://" + ip_address + "/"
        if encoding not in ["avc", "mjpg", "mpeg4"]:
            print("Encoding {} is invalid. Reverting to avc.".format(encoding))
            encoding = "avc"
        out += encoding
        if overlay == False:
            out += "?overlay=off"
        return out
    
    def toggle_feed(self):
        if self.stream.stream.isOpened():
            print("Closing the feed..")
            self.stream.stop()
            self.stream.stream.release()
        else:
            print("Opening the feed..")
            self.stream = VideoStream(self.rtsp_url).start()
            self.viewer.vs = self.stream

class CameraViewer:
    # This class opens the camera feed in a window using cv2
    def __init__(self, stream: VideoStream):
        self.vs = stream
        
    def show_video(self, process_func:list = []):
        """
        Opens a window showing the video feed from the thermal camera. Optionally accepts a process func, which can be used to manipulate the raw image before displaying.
        
        Example:
            # the first argument to the process function must be the raw frame!
            def gray_resize(frame, w, h):
                out = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                out = cv2.resize(out, (w, h))
                return out
            
            cam.viewer.show_video([gray_resize, 1024, 768])

        Parameters
        ----------
        process_func : list, optional
            A list with the process function and its arguments. The default is [].

        Returns
        -------
        None.

        """
        if not self.vs.stream.isOpened():
            print("Stream is not open.")
            return
        cv2.destroyAllWindows()
        t = threading.Thread(target = self.update, name = "CameraViewer", args = process_func)
        t.daemon = True
        t.start()
    
    def update(self, *process_func):
        while True:
            if not self.vs.stream.isOpened():
                print("Stream closed.")
                return
            frame = self.vs.read()
            if len(process_func) > 0:
                frame = process_func[0](frame, *process_func[1:])
            if frame is None:
                continue
            cv2.putText(frame, "Press 'q' to close", (5, 15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255))
            cv2.imshow('output', frame)
            key = cv2.waitKey(1) & 0xFF     
            if key == ord('q'):
                break
        return

# def gray_resize(frame, w, h):
#     out = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     out = cv2.resize(out, (w, h))
#     return out
    
# cam = Ax8CameraFeed("192.168.1.111")
# print("Number of threads", threading.active_count()) 