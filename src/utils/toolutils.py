# %%
# -*- coding: utf-8 -*-
"""
Created on Fri 2022/03/18 09:00:00

@author: Chang Jie
"""
import time
import numpy as np
import pandas as pd

import cv2 # pip install opencv-python
import serial # pip install pyserial
import serial.tools.list_ports
import pyvisa as visa # pip install -U pyvisa

RASP_PI = False
DEMO_CAM_PATH = 'demo/demo_cam.png'
DEMO_IRC_PATH = 'demo/demo_irc.png'
try:
    import sys
    sys.path.append('/home/pi/Desktop/Automated Tools/src/code')
    sys.path.append('/home/pi/Desktop/Automated Tools/src/code/thermal')
    DEMO_CAM_PATH = '/home/pi/Desktop/Automated Tools/src/code/demo/demo_cam.png'
    DEMO_IRC_PATH = '/home/pi/Desktop/Automated Tools/src/code/demo/demo_irc.png'
    RASP_PI = True
except:
    pass
# from thermal.ax8 import Ax8ThermalCamera
from debugger import Debugger
debug = Debugger(show_logs=True)
print(f"Import: OK <{__name__}>")


# %% Serial / CNC
def display_ports():
    """
    Displays available ports.
    """
    ports = serial.tools.list_ports.comports()
    for port, desc, hwid in sorted(ports):
        print("{}: {} [{}]".format(port, desc, hwid))
    if len(ports) == 0:
        print("No ports detected!")
        print("Simulating platform...")
    return


class CNC(object):
    """
    Controller for cnc xyz-movements.
    - address: serial address of cnc Arduino
    """
    def __init__(self, address):
        self.address = address
        self.current_x = 0
        self.current_y = 0
        self.current_z = 0
        self.space_range = [(0,0,0), (0,0,0)]
        self.Z_safe = np.nan
        return

    def move(self, axis, displacement):
        """
        Move cnc in one axis and displacement
        - axis: X, Y, or Z
        - displacement: displacement in mm
        """
        axis = axis.upper()
        vector = (0,0,0)    
        if axis == 'X':
            vector = (displacement,0,0) 
        elif axis == 'Y':
            vector = (0,displacement,0) 
        elif axis =='Z':
            vector = (0,0,displacement) 
        return self.move_3axis(vector, z_to_safe=True)

    def move_3axis(self, vector, z_to_safe=True):
        """
        Move cnc in all axes and displacement
        - vector: vector in mm
        """
        x, y, z = vector
        next_x = round(self.current_x + x, 2)
        next_y = round(self.current_y + y, 2)
        next_z = round(self.current_z + z, 2)
        next_pos = (next_x, next_y, next_z)
        return self.to_position(next_pos, z_to_safe)
    
    def to_position(self, coord, z_to_safe=True):
        """
        Move cnc to absolute position in 3D
        - coord: (X, Y, Z) coordinates of target
        """
        if z_to_safe and self.current_z < self.Z_safe:
            try:
                self.cnc.write(bytes("G90\n", 'utf-8'))
                print(self.cnc.readline())
                self.cnc.write(bytes(f"G0 Z{self.Z_safe}\n", 'utf-8'))
                print(self.cnc.readline())
                self.cnc.write(bytes("G90\n", 'utf-8'))
                print(self.cnc.readline())
            except:
                pass
            self.current_z = self.Z_safe
            print(f'{self.current_x}, {self.current_y}, {self.current_z}')
        
        x, y, z = coord
        z_first = True if self.current_z<z else False
        l_bound, u_bound = np.array(self.space_range)
        next_pos = np.array(coord)

        if all(np.greater_equal(next_pos, l_bound)) and all(np.less_equal(next_pos, u_bound)):
            pass
        else:
            print(f"Range limits reached! {self.space_range}")
            return

        positionXY = f'X{x}Y{y}'
        position_Z = f'Z{z}'
        moves = [position_Z, positionXY] if z_first else [positionXY, position_Z]
        try:
            self.cnc.write(bytes("G90\n", 'utf-8'))
            print(self.cnc.readline())
            for move in moves:
                self.cnc.write(bytes(f"G0 {move}\n", 'utf-8'))
                print(self.cnc.readline())
            self.cnc.write(bytes("G90\n", 'utf-8'))
            print(self.cnc.readline())
        except:
            pass

        self.current_x = x
        self.current_y = y
        self.current_z = z
        print(f'{self.current_x}, {self.current_y}, {self.current_z}')
        return


class Ender(CNC):
    """
    XYZ controls for Ender platform.
    - address: serial address of cnc Arduino
    - space_range: range of motion of tool
    """
    def __init__(self, address, space_range=[(0,0,0), (240,235,210)], Z_safe=30):
        super().__init__(address)
        self.cnc = self.connect_cnc(address)
        self.space_range = space_range
        self.Z_safe = Z_safe
        self.home()
        return
    
    def connect_cnc(self, address):
        """
        Establish serial connection to cnc controller.
        - address: port address

        Return: serial.Serial object
        """
        cnc = None
        try:
            cnc = serial.Serial(address, 115200)
        except:
            pass
        return cnc

    def heat(self, bed_temp):
        """
        Heat bed to temperature
        - bed_temp: bed temperature

        Return: bed_temp
        """
        bed_temp = round( min(max(bed_temp,0), 110) )
        try:
            self.cnc.write(bytes('M140 S{}\n'.format(bed_temp), 'utf-8'))
        except:
            print('Unable to heat stage!')
            bed_temp = None
        return bed_temp

    def home(self):
        """
        Homing cycle for Ender platform
        """
        try:
            self.cnc.write(bytes("G90\n", 'utf-8'))
            print(self.cnc.readline())
            self.cnc.write(bytes("G0 " + f"Z{self.Z_safe}" + "\n", 'utf-8'))
            print(self.cnc.readline())
            self.cnc.write(bytes("G90\n", 'utf-8'))
            print(self.cnc.readline())

            self.cnc.write(bytes("G28\n", 'utf-8'))

            self.cnc.write(bytes("G90\n", 'utf-8'))
            print(self.cnc.readline())
            self.cnc.write(bytes("G0 " + f"Z{self.Z_safe}" + "\n", 'utf-8'))
            print(self.cnc.readline())
            self.cnc.write(bytes("G90\n", 'utf-8'))
            print(self.cnc.readline())
        except:
            pass
        self.current_x = 0
        self.current_y = 0
        self.current_z = self.Z_safe
        try:
            self.cnc.write(bytes("G1 F10000\n", 'utf-8'))
            print(self.cnc.readline())
        except:
            pass
        return

    
class Primitiv(CNC):
    """
    XYZ controls for Primitiv platform.
    - address: serial address of cnc Arduino
    - space_range: range of motion of tool
    """
    def __init__(self, address, space_range=[(-410,-290,-120), (0,0,0)], Z_safe=-80, Z_updown=(-94,-104)):
        super().__init__(address)
        self.cnc = self.connect_cnc(address)
        self.space_range = space_range
        self.selected_position = ''
        self.Z_safe = Z_safe
        self.Z_up, self.Z_down = Z_updown
        return
    
    def connect_cnc(self, address):
        """
        Establish serial connection to cnc controller.
        - address: port address

        Return: serial.Serial object
        """
        cnc = None
        try:
            cnc = serial.Serial(address, 115200, timeout=1) 
            cnc.close()
            cnc.open()

            # Start grbl 
            cnc.write(bytes("\r\n\r\n", 'utf-8'))
            time.sleep(2)
            cnc.flushInput()

            # Homing cycle
            cnc.write(bytes("$H\n", 'utf-8'))
            print(cnc.readline())
            print("CNC ready")
        except:
            pass
        return cnc
    
    def home(self):
        """XYZ-zero"""
        try:
            self.cnc.write(bytes("$H\n", 'utf-8'))
            print(self.cnc.readline())
        except:
            pass
        
        self.current_x = 0
        self.current_y = 0
        self.current_z = 0
        print(f'{self.current_x}, {self.current_y}, {self.current_z}')


# %% Keithley
class Keithley(object):
    """
    Keithley relay.
    - address: (short) IP address of Keithley
    - settings: settings to be applied
    - numreadings: number of readings at each I-V combination
    - buffersize: size of buffer
    - name: nickname for Keithley
    """
    def __init__(self, address, name=''):
        print(f"\nSetting up {name.title()} Keithley comms...")
        
        self.address = address
        self.name = name
        self.numreadings = 0
        self.buffersize = 0
        self.buffer = ''
        self.buffer_df = pd.DataFrame()

        self.inst = self.connect(address)
        self.getI = ''
        self.getV = ''
        
        print(f"{self.name.title()} Keithley ready")
        pass
    
    def apply_settings(self, settings, source, numreadings, buffersize=100):
        """
        Apply settings to Keithley
        - settings: list of strings to be fed to Keithley
        - numbreadings: number of readings per measurement
        - buffersize: buffer size

        Return: str, str (tags for reading I,V data)
        """
        self.numreadings = numreadings
        self.buffersize = buffersize
        self.buffer = f'"{self.name}data"'
        count = f'sense:count {numreadings}'
        makebuffer = f'trace:make {self.buffer}, {buffersize}'
        if source == 'V':
            getV = f'trace:data? 1, {numreadings}, {self.buffer}, SOUR'
            getI = f'trace:data? 1, {numreadings}, {self.buffer}, READ'
        elif source== 'I':
            getI = f'trace:data? 1, {numreadings}, {self.buffer}, SOUR'
            getV = f'trace:data? 1, {numreadings}, {self.buffer}, READ'

        try:
            for setting in settings:
                self.inst.write(setting)
            self.inst.write(count)
            self.inst.write(makebuffer)
        except Exception as e:
            print(e)
            pass
        return getI, getV

    def connect(self, address):
        """
        Establish connection with Keithley
        - address: (short) IP address of Keithley

        Return: Keithley instance
        """
        inst = None
        try:
            full_address = f"TCPIP0::192.168.1.{address}::5025::SOCKET"
            rm = visa.ResourceManager('@py')
            inst = rm.open_resource(full_address)

            inst.write_termination = '\n'
            inst.read_termination = '\n'
            inst.write(':syst:beep 500,1')
            inst.query('*IDN?')
        except Exception as e:
            print("Unable to connect to Keithley!")
            print(e)
            pass
        return inst

    def read_data(self):
        """
        Read data from Keithley and saving to self.buffer_df
        """
        n = self.name[0]
        volt = 0
        try:
            self.inst.write(self.getV)
            volt = None
        except:
            pass
        while volt is None:
            try:
                volt = self.inst.read()
            except:
                pass
        debug.show_print(f"V{n} done")
        volt_split = volt.split(',')

        curr = 0
        try:
            self.inst.write(self.getI)
            curr = None
        except:
            pass
        while curr is None:
            try:
                curr = self.inst.read()
            except:
                pass
        debug.show_print(f"I{n} done")
        curr_split = curr.split(',')
        
        row = np.column_stack((volt_split, curr_split)).astype('float64')
        data_row = pd.DataFrame(row, columns = [f'V{n}', f'I{n}'])
        self.buffer_df = pd.concat([self.buffer_df, data_row])
        return

    def set_parameters(self, params=[]):
        """
        Relay parameters to Keithley
        - params: list of parameters to write to Keithley
        """
        try:
            for param in params:
                self.inst.write(param)
        except:
            pass
        return


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


# %% Thermal
# class Thermal(Ax8ThermalCamera):
#     def __init__(self, ip_address: str, encoding: str = "avc", overlay: bool = False, verbose: bool = True, cam_size=(640,480)):
#         if RASP_PI:
#             try:
#                 super().__init__(ip_address, encoding, overlay, verbose)
#             except:
#                 pass
#         self.cam_size = cam_size
#         return

#     def read_image(self, crosshair=True):
#         """
#         Retreive image from camera capture
#         - crosshair: whether to display crosshair on image

#         Return: bool, image
#         """
#         ret = False
#         try:
#             frame = self.video.stream.read()
#             frame = self.rotate180(frame)
#             ret = True
#         except:
#             frame = cv2.imread(DEMO_IRC_PATH)
#             ret = True
#         if ret:
#             frame = cv2.resize(frame, self.cam_size)

#             # Create crosshair in center of image
#             if crosshair:
#                 center_x = int(frame.shape[1] / 2)
#                 center_y = int(frame.shape[0] / 2)
#                 cv2.line(frame, (center_x, center_y+50), (center_x, center_y-50), (255,255,255), 1)
#                 cv2.line(frame, (center_x+50, center_y), (center_x-50, center_y), (255,255,255), 1)
#         return ret, frame

#     def rotate180(self, frame):
#         """
#         Rotate the frame by 180 degrees
#         - frame: image

#         Return: rotated image
#         """
#         frame = cv2.rotate(frame, cv2.ROTATE_180)
#         return frame

