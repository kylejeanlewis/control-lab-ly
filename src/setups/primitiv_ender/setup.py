# %%
# -*- coding: utf-8 -*-
"""
Created on Fri 2022/03/18 09:00:00

@author: Chang Jie
"""
import os, sys
import time
from datetime import date, datetime
import numpy as np
import pandas as pd
import threading
import matplotlib.pyplot as plt

from PySimpleGUI import WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT

THERE = {
    'movement': 'utils\\movement', 
    'electrical': 'utils\\characterisation\\electrical', 
    'image': 'utils\\image',
    'demo': 'utils\\image\\demo',
    'thermal': 'utils\\image\\thermal',
    'ax8': 'utils\\image\\thermal\\ax8',
    'gui': 'utils\\gui',
    'misc': 'utils\\misc'
}
here = os.getcwd()
base = here.split('src')[0] + 'src'
there = {k: '\\'.join([base,v]) for k,v in THERE.items()}
for v in there.values():
    sys.path.append(v)

from cartesian_utils import Primitiv, Ender
from keithley_utils import Keithley
from image_recognition import Vision
from thermal_cam import Thermal
from guibuilder import Builder, Popups
from miscfunctions import Debugger
print(f"Import: OK <{__name__}>")

pop = Popups()
debug = Debugger()

ADDRESS_PRIMITIV = ['/dev/ttyACM0']
ADDRESS_ENDER = ['/dev/ttyUSB0', '/dev/ttyUSB1']
XMLPATH = '/home/pi/Desktop/Automated Tools/src/Image classifiers/haarcascade_ossila.xml'

class Setup(object):
    """
    Basic tool setup.
    - platform: physical platform class the tool is based on
    - z_updown: up and down Z-positions of probe
    - default_cam: default position of camera
    - probe_offset: x,y offset from camera to probe
    - calib_unit: calibration unit between on-camera distance and physical distance
    """
    def __init__(self, platform_class=None, z_updown=(0,0), default_cam=(0,0), probe_offset=(0,0), calib_unit=1):
        if 'Primitiv' in str(platform_class):
            platform = platform_class(ADDRESS_PRIMITIV[0])
            pass
        elif 'Ender' in str(platform_class):
            try:
                platform = platform_class(ADDRESS_ENDER[0])
            except:
                platform = platform_class(ADDRESS_ENDER[1])
            pass
        
        self.window = None
        self.name = ''
        self.controls = []
        self.devices = []
        self.threads = {}
        
        self.platform = platform
        self.z_up = z_updown[0]
        self.z_down = z_updown[1]
        self.update_position = False
        
        self.def_cam = default_cam
        self.probe_offset = probe_offset
        self.calib_cam = default_cam
        self.calib_probe = (default_cam[0]+probe_offset[0], default_cam[1]+probe_offset[1])
        self.calib_unit = calib_unit
        self.vision = Vision(calib_unit)
        self.freeze_cam = False
        self.frame_display = None
        self.positions_df = pd.DataFrame()
        self.rectangles_df = pd.DataFrame()

        self.thermal = None

        self.savefolder = ''
        self.savepath = ''
        self.csvpath = ''
        self.imgpath = ''
        self.xmlpath = ''

        self.time_start = round(time.time())
        self.time_elapsed = round(time.time())
        self.time_estimate = round(time.time())
        self.estimate_time = False
        self.stop_measure = True
        self.disable_buttons = False
        return
    
    # Main methods (build_window, gui_loop, run_program)
    def build_window(self):
        """
        Build GUI window from blocks provided in guibuilder.Builder object
        """
        bd = Builder()
        bd.addLayout('-FINAL-', [[bd.getB('Ok', (20,5))]])
        self.window = bd.getWindow("*")
        return

    def gui_loop(self, paths={}):
        """
        Run a loop to keep GUI window open
        - paths: dict of paths to save output
        """
        while True:
            event, values = self.window.read(timeout=20)
            ## 0. Exit loop
            if event in ('Ok', WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT, None):
                break
        return

    def run_program(self, paths={}, maximize=False):
        """
        Run program based on build_window and defined gui_loop
        - paths: dict of paths to save output
        - maximize: whether to maximize window
        """
        try:
            savefolder = paths['savefolder']
        except:
            savefolder = ''
        self.savefolder = savefolder
        if len(self.savefolder) == 0:
            self.savefolder = os.getcwd().replace('\\', '/')
        elif not os.path.exists(self.savefolder):
            os.makedirs(self.savefolder)
        
        self.build_window()
        self.window.Finalize()
        if maximize:
            self.window.Maximize()
        self.window.bring_to_front()
        self.gui_loop(paths)
        self.window.close()
        return

    # Other methods
    def convert_time_to_string(self, total_time):
        """
        Display time duration (s) as H:M:S text
        - total_time: duration in seconds

        Return: str
        """
        m, s = divmod(total_time, 60)
        h, m = divmod(m, 60)
        return f'{int(h):02}hr {int(m):02}min {int(s):02}sec'

    def default_view(self):
        """
        Move to preset camera position, taking camera position
        """
        stage = self.platform
        x, y = self.def_cam
        z = 0
        
        stage.moveTo((x,y,z))
        stage.selected_position = 'camera'
        print("At camera position")
        return
    
    def display_current_image(self):
        """
        Display current image in self.frame_display
        """
        imgbytes = self.vision.encode(self.frame_display)
        self.window['-IMAGE-'].update(data=imgbytes)
        return

    def display_saved_img(self, update_display=True):
        """
        Display image from file
        """
        img = self.vision.load(self.imgpath)
        self.frame_display = img
        self.freeze_cam = True
        self.update_position = True
        if update_display:
            self.display_current_image()
        return img

    def record_temperature(self, timeout=300):
        cam = self.thermal
        cam.video.toggle_feed()
        data = []
        while len(data) <=timeout:
            try:
                temp1, temp2 = cam.get_spotmeter_temps([1,2])
            except:
                continue
            data.append((datetime.now().strftime('%H:%M:%S'), temp1, temp2))
            time.sleep(1)
        df = pd.DataFrame(data, columns=['time', 'temp1', 'temp2'])
        return df
    
    def set_all_buttons(self, disable=True):
        """
        Set the state of all buttons
        - disable: whether to disable all buttons
        """
        for _, ele in self.window.key_dict.items():
            if 'Button' in str(type(ele)):
                ele.update(disabled=disable)
        self.disable_buttons = disable
        return

    def switch(self, final):
        """
        Switch between camera and probe positions.
        - final: intended final position
        """
        stage = self.platform
        initial = stage.selected_position

        if final not in ['camera', 'probe']:
            return
        if initial == final:
            print(f'Already at {final} position!')
            return
        elif final == 'probe':
            x = stage.current_x + self.probe_offset[0]
            y = stage.current_y + self.probe_offset[1]
            z = stage.current_z
        elif final == 'camera':
            x = stage.current_x - self.probe_offset[0]
            y = stage.current_y - self.probe_offset[1]
            z = stage.current_z
        stage.moveTo((x,y,z))
        stage.selected_position = final
        print(f"At {final} position")
        return
 

# %%
class BasicMovement(Setup):
    """
    Basic GUI for movement control.
    - platform_class: physical platform class the tool is based on
    """
    def __init__(self, platform_class):
        super().__init__(platform_class)
        self.name = 'move'
        self.update_position = False
        return
    
    def build_window(self):
        """
        Build GUI window from blocks provided in guibuilder.Builder object
        """
        bd = Builder()
        bd.addLayout('-FINAL-', [
            [bd.getXYZControls()],
            [bd.getTitle("", (64,1))],
            [bd.getPositions()]
            ], alignV='top')
        self.window = bd.getWindow("XYZ-stage controls")
        return
    
    def gui_loop(self, paths={}):
        """
        Run a loop to keep GUI window open
        - paths: dict of paths to save output
        """
        stage = self.platform

        movement_buttons = {}
        for axis in ['X', 'Y', 'Z']:
            for displacement in ['-10', '-1', '-0.1', '+0.1', '+1', '+10']:
                movement_buttons[axis+displacement] = (axis, displacement)
        
        while True:
            event, values = self.window.read(timeout=20)
            ## 0. Exit loop
            if event in (WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT, None):
                break
            
            # Event handler #
            ## 1. XYZ control
            if event in ('<XY>', '<Z>', 'Go To', 'Reset'):
                self.update_position = True
            ### 1.1 Home
            if event in ('<XY>', '<Z>'):
                stage.home()
            ### 1.2 XYZ buttons
            if event in movement_buttons.keys():
                axis, displacement = movement_buttons[event]
                stage.move(axis, float(displacement))
                self.update_position = True
            ### 1.3 Go To Position
            if event == 'Go To':
                x = float(values['-X-CURRENT-'])
                y = float(values['-Y-CURRENT-'])
                z = float(values['-Z-CURRENT-'])
                stage.moveTo((x,y,z))
            if self.update_position:
                self.window['-X-CURRENT-'].update(stage.current_x)
                self.window['-Y-CURRENT-'].update(stage.current_y)
                self.window['-Z-CURRENT-'].update(stage.current_z)
                self.update_position = False
        return


# %%
class FieldEffectTransistor(Setup):
    """
    Typical setup for FET measurements.
    - platform: physical platform class the tool is based on
    - z_updown: 2-ple of up & down Z-positions
    - default_cam: 2-ple of camera's x,y position of default view
    - probe_offset: 2-ple of probe's x,y offset
    - calib_unit: image-to-physical unit conversion
    """
    def __init__(self, platform_class=Primitiv, z_updown=(0,0), default_cam=(0,0), probe_offset=(0,0), calib_unit=1):
        super().__init__(platform_class, z_updown, default_cam, probe_offset, calib_unit)
        self.name = 'fet'
        self.gate = None
        self.drain = None
        self.thermal = Thermal("192.168.1.111")
        self.v_ranges = {'idvd_G': (-30, 31, 10), 'idvd_D': (-25, 26, 1), 'idvg_D': (-10, 11, 2), 'idvg_G': (-50, 51, 1)}
        return
    
    def build_window(self):
        """
        Build GUI window from blocks provided in guibuilder.Builder object
        """        
        bd = Builder()
        bd.addLayout('-CAM-MACROS-', [
            [bd.getCamera()],
            [bd.getPositions()],
            [bd.getTitle("", (64,1))],
            [bd.getMacros(['Save Data', 'Check', 'Switch Ctrl'])],
            [bd.getTitle("", (64,1))]
            ], alignV='top')
        bd.addCollapsable('-OPENCV-', [[bd.getOpenCV()], [bd.getFile('XML', XMLPATH)]])
        bd.addCollapsable('-KEITHLEY-', [
            [bd.getTitle("Keithley Control (Voltage)", (64,1), 'center', bold=True)],
            [bd.getKeithleyParams('drain', 104, self.v_ranges["idvd_D"])],
            [bd.getP(), bd.getText(f'Id-Vd, drain: {self.v_ranges["idvd_D"]}', key='-IDVD-D-'), bd.getP(), 
            bd.getText(f'Id-Vg, drain: {self.v_ranges["idvg_D"]}', key='-IDVG-D-'), bd.getP()],
            [bd.getKeithleyParams('gate', 116, self.v_ranges["idvd_G"])],
            [bd.getP(), bd.getText(f'Id-Vd, gate: {self.v_ranges["idvd_G"]}', key='-IDVD-G-'), bd.getP(), 
            bd.getText(f'Id-Vg, gate: {self.v_ranges["idvg_G"]}', key='-IDVG-G-'), bd.getP()],
            [bd.getP(), bd.getB('Set Id-Vd', (8,1)), bd.getP(), bd.getB('Set Id-Vg', (8,1)), bd.getP()],
            [bd.getFolder('SAVE', self.savefolder)],
            [bd.getText("Sample ID: ", (20,1)), bd.getI('sample', (36,1), "-SAMPLE ID-"), bd.getB('Measure', (8,1))],
            ], alignV='top')
        bd.addCollapsable('-TIMER-', [
            [bd.getText('Time elapsed: ', (20,1)), bd.getText('Waiting for estimate!', (20,1), key='-TIME ELAPSED-')],
            [bd.getText('Time estimate: ', (20,1)), bd.getText('Waiting for estimate!', (20,1), key='-TIME ESTIMATE-')],
            [bd.getText('Time left: ', (20,1)), bd.getText('Waiting for estimate!', (20,1), key='-TIME LEFT-')],
            [bd.getB('Stop Measurement', (20,1), key='-STOP MEASURE-')]
            ], alignV='top')
        bd.addLayout('-XYZ-CTRL-', [
            [bd.getXYZControls()],
            [bd.layouts['-OPENCV-']],
            [bd.layouts['-KEITHLEY-']],
            [bd.layouts['-TIMER-']]
            ], alignV='top')
        
        self.controls = ['-KEITHLEY-', '-OPENCV-']
        bd.addLayout('-FINAL-', [[bd.layouts['-CAM-MACROS-'], bd.layouts['-XYZ-CTRL-']]], alignV='top')
        self.window = bd.getWindow("Primitiv FET Measurement")
        return
  
    def gui_loop(self, paths={}):
        """
        Run a loop to keep GUI window open
        - paths: dict of paths to save output
        """
        try:
            xmlpath = paths['xmlpath']
        except:
            xmlpath = ''
        self.xmlpath = xmlpath

        stage = self.platform
        vis = self.vision
        data = {}
        df = pd.DataFrame()

        recalib_cam = False
        recalib_probe = False
        movement_buttons = {}
        for axis in ['X', 'Y', 'Z']:
            for displacement in ['-10', '-1', '-0.1', '+0.1', '+1', '+10']:
                movement_buttons[axis+displacement] = (axis, displacement)
        
        # Window modifications
        controls = self.controls
        curr_ctrl = 0
        for control in controls:
            self.window[control].update(visible=False)
        self.window[controls[curr_ctrl]].update(visible=True)
        self.window['-TIMER-'].update(visible=False)
        self.window['-SAMPLE ID-'].set_focus(True)

        while True:
            event, values = self.window.read(timeout=20)
            self.set_all_buttons(disable=self.disable_buttons)
            self.window['-STOP MEASURE-'].update(disabled=False)
            ## 0. Exit loop
            if event in (WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT, None):
                break
            if vis.checkEscapeKey():
                break
            
            ## Event handler ##
            ## 1. XYZ control
            if event in ('<XY>', '<Z>', 'Go To', 'Reset'):
                self.update_position = True
            ### 1.1 Home
            if event in ('<XY>', '<Z>'):
                stage.home()
            ### 1.2 XYZ buttons
            if event in movement_buttons.keys():
                axis, displacement = movement_buttons[event]
                stage.move(axis, float(displacement))
                self.update_position = True
            ### 1.3 Go To Position
            if event == 'Go To':
                x = float(values['-X-CURRENT-'])
                y = float(values['-Y-CURRENT-'])
                z = float(values['-Z-CURRENT-'])
                stage.moveTo((x,y,z))
            if self.update_position:
                self.window['-X-CURRENT-'].update(stage.current_x)
                self.window['-Y-CURRENT-'].update(stage.current_y)
                self.window['-Z-CURRENT-'].update(stage.current_z)
                self.update_position = False

            ## 2. Macro buttons
            if event in ('-SAVEDATA-', '-CHECK-', 'Measure', '-IMAGE-'):
                today = date.today().strftime("%Y-%m-%d")
                savefolder = values['-SAVE FOLDER-']
                saveid = values['-SAMPLE ID-']
                savepath = f'{savefolder}/{today}/OUTPUT {saveid}'
                self.savepath = savepath
                if not os.path.exists(savepath):
                    os.makedirs(savepath)
                self.csvpath = f'{savepath}/positions_{saveid}.csv'
                self.imgpath = f'{savepath}/haarcascade_{saveid}.png'
                self.update_position = True
            if event in ('Default View', 'Probe', 'Cam'):
                self.update_position = True
            if event == 'Default View':
                self.default_view()
            if event == 'Set View':
                self.def_cam = (stage.current_x, stage.current_y)
                pop.notif('Set!')
            if event == 'Probe':
                self.switch('probe')
            if event == 'Cam':        
                self.switch('camera')
            if event == 'Calibrate':
                if stage.selected_position == 'camera':
                    self.calib_cam = (stage.current_x, stage.current_y)
                    recalib_cam = True
                    pop.notif('Set!')
                elif stage.selected_position == 'probe':
                    self.calib_probe = (stage.current_x, stage.current_y)
                    recalib_probe = True
                    pop.notif('Set!')
                if recalib_cam and recalib_probe:
                    offset_x = self.calib_probe[0] - self.calib_cam[0]
                    offset_y = self.calib_probe[1] - self.calib_cam[1]
                    self.probe_offset = (offset_x, offset_y)
                    recalib_cam, recalib_probe = False, False
            if event == '-SAVEDATA-':
                self.rectangles_df = df
                self.save_data(data, self.frame_display, self.csvpath, self.imgpath)
                pop.notif('Saved!')
            if event == '-CHECK-':
                self.display_saved_img()
                try:
                    thread = threading.Thread(target=self.make_contact, name=f'check', daemon=False)
                    thread.start()
                    self.threads['check'] = thread
                    # self.threads['check'].join(timeout=60)
                except:
                    pass
                pass
            if event == '-SWITCHCTRL-':
                self.window[controls[curr_ctrl]].update(visible=False)
                curr_ctrl = (curr_ctrl+1)%len(controls)
                self.window[controls[curr_ctrl]].update(visible=True)
            
            ## 3. Measurements
            if event == 'Measure':
                try:
                    self.positions_df = pd.read_csv(self.csvpath, index_col=0)
                    self.positions_df.columns = ["X","Y"]
                    print("Checking positions")
                
                    self.display_saved_img()
                    self.gate = None
                    self.drain = None
                    self.gate = self.configure_Keithley(values['-G-ADDRESS-'], 'gate')
                    self.drain = self.configure_Keithley(values['-D-ADDRESS-'], 'drain')
                    
                    self.devices = np.arange(len(self.positions_df)) + 1
                    self.devices = pop.listbox(self.devices, "Check connections!\nSelect devices:", '-DEVICES-')
                    self.time_start = round(time.time())
                    self.time_elapsed = round(time.time())
                    self.time_estimate = round(time.time())
                    self.window['-TIME ESTIMATE-'].update(value='Waiting for estimate!')
                    self.window['-TIME LEFT-'].update(value='Waiting for estimate!')
                    self.window['-TIMER-'].update(visible=True)
                    self.stop_measure = False

                    try:
                        thread = threading.Thread(target=self.make_contact, args=[True], name=f'measure', daemon=False)
                        thread.start()
                        self.threads['measure'] = thread
                        # self.threads['measure'].join(timeout=60)
                    except:
                        pass
                except:
                    print("File not found")
                    print(f"Attempted: {self.csvpath}")
                    if len(self.csvpath) == 0:
                        print("Please input path to csv file")
            if event == '-STOP MEASURE-':
                self.stop_measure = True
                self.set_all_buttons(disable=False)
                pass

            ## 4. Vision control
            ret = False
            if not self.freeze_cam:
                ret, frame = vis.read_image()
            ### 4.1 Receive inputs from GUI window
            xmlpath = values['-XML FILE-']
            pause = values["-PAUSE DETECT-"]
            beta = int(values["-BRIGHTNESS SLIDER-"])
            alpha = int(values["-CONTRAST SLIDER-"])
            scale_factor = 1 + (int(values["-SCALE SLIDER-"]) / 1000)
            neighbors = int(values["-NEIGHBOR SLIDER-"])
            opening_iter = int(values["-OPENING SLIDER-"])
            closing_iter = int(values["-CLOSING SLIDER-"])
            if values["-KERNEL DISABLE-"]:
                blur_kernel = 0 
            elif values["-3x3 KERNEL SIZE-"]:
                blur_kernel = 3
            elif values["-5x5 KERNEL SIZE-"]:
                blur_kernel = 5
            elif values["-9x9 KERNEL SIZE-"]:
                blur_kernel = 9
            ### 4.2 Process and detect target
            if ret:
                frame = vis.process(frame, alpha, beta, blur_kernel)
                if not pause:
                    if self.xmlpath != xmlpath:
                        if os.path.exists(xmlpath) and xmlpath.endswith('.xml'):
                            self.xmlpath = xmlpath
                            vis.cascade = vis.getClassifier(xmlpath)
                        else:
                            pop.notif('Unable to load XML data!')
                            self.window["-PAUSE DETECT-"].update(value=True)
                    if type(vis.cascade) != type(None):
                        df = vis.detect(frame, scale_factor, neighbors)
                        data, frame = vis.annotate(df, frame, opening_iter, closing_iter)
                self.frame_display = frame
                self.display_current_image()
            ### 4.3 Manually locating targets
            if event == '-IMAGE-':
                self.window["-PAUSE DETECT-"].update(value=True)
                ret, frame = vis.read_image(crosshair=False)
                if ret:
                    data = pop.draw_rectangles(data=vis.encode(frame), img_size=vis.cam_size)
                    if len(data):
                        df = vis.data_to_df(data)
                        data, frame = vis.annotate(df, frame)
                        self.rectangles_df = df
                        self.save_data(data, frame, self.csvpath, self.imgpath)
                        pop.notif('Saved!')

            ## 5. Keithley
            if event == 'Set Id-Vd':
                v_range_G = (int(values['-G-START-']), int(values['-G-STOP-']), int(values['-G-STEP-']))
                v_range_D = (int(values['-D-START-']), int(values['-D-STOP-']), int(values['-D-STEP-']))
                self.v_ranges['idvd_G'] = v_range_G
                self.v_ranges['idvd_D'] = v_range_D
                self.window['-IDVD-G-'].update(value=f'Id-Vd, gate: {self.v_ranges["idvd_G"]}')
                self.window['-IDVD-D-'].update(value=f'Id-Vd, drain: {self.v_ranges["idvd_D"]}')
            if event == 'Set Id-Vg':
                v_range_D = (int(values['-D-START-']), int(values['-D-STOP-']), int(values['-D-STEP-']))
                v_range_G = (int(values['-G-START-']), int(values['-G-STOP-']), int(values['-G-STEP-']))
                self.v_ranges['idvg_D'] = v_range_D
                self.v_ranges['idvg_G'] = v_range_G
                self.window['-IDVG-D-'].update(value=f'Id-Vg, drain: {self.v_ranges["idvg_D"]}')
                self.window['-IDVG-G-'].update(value=f'Id-Vg, gate: {self.v_ranges["idvg_G"]}')

            ## 6. Time estimates
            if not self.stop_measure:
                time_elapsed = time.time() - self.time_start
                if self.time_elapsed != time_elapsed:
                    self.time_elapsed = time_elapsed
                    self.window['-TIME ELAPSED-'].update(value=self.convert_time_to_string(self.time_elapsed))
                    if self.time_estimate != self.time_start:
                        time_left = round(self.time_estimate - self.time_elapsed)
                        self.window['-TIME LEFT-'].update(value=self.convert_time_to_string(time_left))
                    if self.estimate_time:
                        time_left = round(self.time_estimate - self.time_elapsed)
                        self.window['-TIME ESTIMATE-'].update(value=self.convert_time_to_string(self.time_estimate))
                        self.estimate_time = False

            self.display_current_image()

        vis.close()
        return
    
    def configure_Keithley(self, address, name='', settings=[]):
        """
        Establish connection with Keithley
        - address: (short) IP address of Keithley
        - name: name of Keithley
        - settings: settings to be applied

        Return: toolutils.Keithley object
        """
        if len(settings) == 0:
            settings = [
                '*RST',
                # 'sense:current:OCOM ON',
                # 'ROUT:TERM REAR',
                'SOUR:FUNC VOLT',
                'SOUR:VOLT:RANG 200',
                'SOUR:VOLT:ILIM 0.01',

                'SENS:FUNC "CURR"',
                'SENSE:CURR:rsense OFF',
                'SENS:CURR:RANGE 10E-6',
                'sense:current:UNIT AMP'
            ]
        keithley = Keithley(address, name)
        keithley.getI, keithley.getV = keithley.applySettings(settings, 'V', 5, 100)
        return keithley
  
    def make_contact(self, measure=False):
        """
        Make contact with the saved positions using probe
        - measure: whether to make measurements
        - devices: devices to check/measure
        """
        stage = self.platform
        vis = self.vision
        stage.selected_position = 'probe'
       
        self.disable_buttons = True
        if len(self.devices) == 0:
            self.devices = np.arange(len(self.positions_df)) + 1
        
        count = 0
        for device_n in self.devices:
            device_n = min(device_n, len(self.devices))
            if measure and self.stop_measure:
                break
            x = self.positions_df.iat[device_n-1, 0]
            y = self.positions_df.iat[device_n-1, 1]
            row = self.rectangles_df.iloc[min(device_n-1, len(self.rectangles_df)-1),]
            print(f'{x},{y}')
            print(row)
            self.frame_display = vis.annotate_one(row, self.frame_display, (0,0,255))

            stage.moveTo((x,y,self.z_up))
            self.update_position = True
            if count == 0:
                time.sleep(5)
            time.sleep(1)
            stage.moveTo((x,y,self.z_down))
            self.update_position = True
            time.sleep(1)
            if measure:
                self.make_measurement(self.positions_df.index[device_n-1])
            
            ## Finishing up device
            time.sleep(2)
            stage.moveTo((x,y,self.z_up))
            self.update_position = True
            time.sleep(2)
            count += 1
            self.time_estimate = round((time.time() - self.time_start)/count*len(self.devices))
            self.estimate_time = True
            self.display_saved_img(update_display=False)
        
        self.estimate_time = False
        self.stop_measure = True
        self.freeze_cam = False
        self.disable_buttons = False

        stage.home()
        time.sleep(2)
        self.update_position = True
        self.window['-TIMER-'].update(visible=False)
        return

    def make_measurement(self, device_num):
        """
        Make measurement at the device position using probe
        - device_num: device label
        """
        drain = self.drain
        gate = self.gate
        with open(f'{self.savepath}/parameters.txt', 'w') as file:
            for k, v in self.v_ranges.items():
                print(f'{k}: {v}', file=file)
        print("Starting measurement...")

        tests = ['Id-Vd', 'Id-Vg']
        filename_temp = f'{self.savepath}/Device {device_num}'
        for test in tests:
            if self.stop_measure:
                break
            drain.buffer_df = pd.DataFrame()
            gate.buffer_df = pd.DataFrame()

            if test == 'Id-Vd':
                fixed = gate
                varied = drain
                volts_fixed = np.arange(*self.v_ranges['idvd_G']).tolist()
                volts_varied = np.arange(*self.v_ranges['idvd_D']).tolist()
            elif test == 'Id-Vg':
                fixed = drain
                varied = gate
                volts_fixed = np.arange(*self.v_ranges['idvg_D']).tolist()
                volts_varied = np.arange(*self.v_ranges['idvg_G']).tolist()

            for f in volts_fixed:
                params = [
                    f'SOUR:VOLT {f}',
                    f'trace:clear "{fixed.name}data"',
                    'output ON'
                ]
                fixed.setParameters(params)
                time.sleep(0.5)
                for v in volts_varied:
                    if self.stop_measure:
                        break
                    try:
                        varied.inst.write(f'source:voltage {v}')
                        varied.inst.write(f'trace:clear "{varied.name}data"')
                        fixed.inst.write(f'trace:clear "{fixed.name}data"')
                        varied.inst.write('output ON')
                        varied.inst.write(f'trace:trigger "{varied.name}data"')
                        fixed.inst.write(f'trace:trigger "{fixed.name}data"')
                        drain.readData()
                        gate.readData()
                    except:
                        print(f'Fixed: {f}V | Varied: {v}V')
            try:
                drain.inst.write('output OFF')    
                gate.inst.write('OUTP OFF')
                drain.buffer_df.to_csv(f'{filename_temp} {test}, SD.csv')
                gate.buffer_df.to_csv(f'{filename_temp} {test}, G.csv')
            except:
                pass
        return

    def save_data(self, data, frame, csvpath='', imgpath=''):
        """
        Saves device position data to csv.
        - data: dictionary of device names and coordinates
        - frame: camera feed
        - csvpath: save path for csv data
        - imgpath: save path for image
        """
        print("Saving detection results and device positions ...")
        
        if len(data) == 0:
            print("(Fail) No detection")
        elif len(data) > 0:
            center_x, center_y = self.vision.capture_image(frame, imgpath)

            data = pd.DataFrame(data)
            data = data.T
            data = data.copy()
            data.rename(columns={0: 'x', 1: 'y'},inplace=True)
            # Save CSV file: Coordinates from Center
            data['x'] = (data['x'] - center_x) / self.calib_unit
            data['y'] = (center_y - data['y']) / self.calib_unit
            # Save CSV file: Coordinates from Camera
            data['x'] = data['x'] + self.def_cam[0] 
            data['y'] = data['y'] + self.def_cam[1]
            # Save CSV file: Coordinates from Probe
            data['x'] = data['x'] + self.probe_offset[0]
            data['y'] = data['y'] + self.probe_offset[1]
            data.to_csv(csvpath)
            
            self.positions_df = data
            self.csvpath = csvpath
            print("(Success) Device positions captured")
        return
     

# %%
class FourPointProbe(Setup):
    """
    Typical setup for 4PP measurements.
    - platform: physical platform class the tool is based on
    - z_updown: 2-ple of up & down Z-positions
    - default_cam: 2-ple of camera's x,y position of default view
    - probe_offset: 2-ple of probe's x,y offset
    - calib_unit: image-to-physical unit conversion
    """
    def __init__(self, platform_class=Ender, z_updown=(0,0), default_cam=(0,0), probe_offset=(0,0), calib_unit=1):
        super().__init__(platform_class, z_updown, default_cam, probe_offset, calib_unit)
        self.name = '4pp'
        self.gate = None
        self.thermal = Thermal("192.168.1.120")

        self.amp_range = (-5e-9, 5e-9, 1e-10)

        cols = ['operation_tag', 'time', 'temperature', 'voltage']
        self.buffer_df = pd.DataFrame({col: [] for col in range(len(cols))}, columns=cols)
        self.threads_active = True
        self.operation_tag = 'IDLE'
        return
    
    def build_window(self):
        """
        Build GUI window from blocks provided in guibuilder.Builder object
        """        
        bd = Builder()
        size = (8,1)
        bd.addLayout('-CAM-MACROS-', [
            [bd.getCamera()],
            [bd.getPositions()],
            [bd.getTitle("", (64,1))],
            [bd.getMacros(['Capture', 'Exit', 'Switch Ctrl'])],
            [bd.getTitle("", (64,1))]
            ], alignV='top')
        bd.addCollapsable('-KEITHLEY-', [
            [bd.getTitle("Keithley Control", (64,1), 'center', bold=True)],
            [bd.getKeithleyParams('gate', 116, self.amp_range)],
            [bd.getP(), bd.getText(f'Id-Vg, gate: {self.amp_range}', key='-IDVG-G-'), bd.getP()],
            [bd.getP(), bd.getB('Set Id-Vg', (8,1)), bd.getP()],
            [bd.getText("Bed Temperature: ", (20,1)), bd.getI('25', (36,1), "-BED TEMP-"), bd.getB('Set Temp', (8,1))]
            ], alignV='top')
        bd.addCollapsable('-HYSTERESIS-', [
            [bd.getTitle("Keithley Control (Hysteresis)", (64,1), 'center', bold=True)],
            [bd.getText(f"Source Current Parameters", (64,1), bold=True)],
            [bd.getP(), bd.getText('Address:  ', size, 'right'), bd.getI(116, size, f'-SM-ADDRESS-'), 
            bd.getText('Current:  ', size, 'right'), bd.getI(1e-7, size, f'-SM-CURR-'), 
            bd.getText('Voltage:  ', size, 'right'), bd.getI(2, size, f'-SM-VOLT-'), bd.getP()],
            [bd.getText(f"Temperature Parameters", (64,1), bold=True)],
            [bd.getP(), bd.getText('Hold (s):  ', size, 'right'), bd.getI(45, size, f'-TEMP-HOLD-'),
            bd.getText('High (C):  ', size, 'right'), bd.getI(80, size, f'-TEMP-HI-'), 
            bd.getText('Step (C):  ', size, 'right'), bd.getI(10, size, f'-TEMP-STEP-'), bd.getP()],
            [bd.getP(), bd.getText('Cool (s):  ', size, 'right'), bd.getI(300, size, f'-TEMP-COOL-'), 
            bd.getText('Low (C):  ', size, 'right'), bd.getI(30, size, f'-TEMP-LO-'), 
            bd.getText('# Runs:  ', size, 'right'), bd.getI(1, size, f'-SM-RUNS'), bd.getP()],
            [bd.getText('', size, 'center')]
            ], alignV='top')
        bd.addLayout('-SAVE-DETAILS-', [
            [bd.getFolder('SAVE', self.savefolder)],
            [bd.getText("Sample ID: ", (20,1)), bd.getI('sample', (36,1), "-SAMPLE ID-"), bd.getB('Measure', (8,1))],
            [bd.getP(), bd.getB('Stop Measurement', (20,1), key='-STOP MEASURE-'), bd.getP()]
            ], alignV='top')
        bd.addLayout('-XYZ-CTRL-', [
            [bd.getXYZControls()],
            [bd.layouts['-KEITHLEY-']],
            [bd.layouts['-HYSTERESIS-']],
            [bd.layouts['-SAVE-DETAILS-']]
            ], alignV='top')
        
        self.controls = ['-KEITHLEY-', '-HYSTERESIS-']
        bd.addLayout('-FINAL-', [[bd.layouts['-CAM-MACROS-'], bd.layouts['-XYZ-CTRL-']]], alignV='top')
        self.window = bd.getWindow("Ender 4PP Measurement")
        return
    
    def gui_loop(self, paths={}):
        """
        Run a loop to keep GUI window open
        - paths: dict of paths to save output
        """
        try:
            xmlpath = paths['xmlpath']
        except:
            xmlpath = ''
        self.xmlpath = xmlpath

        stage = self.platform
        vis = self.vision
        thermal = self.thermal
        data = {}

        recalib_cam = False
        recalib_probe = False
        movement_buttons = {}
        for axis in ['X', 'Y', 'Z']:
            for displacement in ['-10', '-1', '-0.1', '+0.1', '+1', '+10']:
                movement_buttons[axis+displacement] = (axis, displacement)
        
        # Window modifications
        controls = self.controls
        curr_ctrl = 0
        for control in controls:
            self.window[control].update(visible=False)
        self.window[controls[curr_ctrl]].update(visible=True)
        self.window['-SAMPLE ID-'].set_focus(True)

        while True:
            event, values = self.window.read(timeout=100)
            self.set_all_buttons(disable=self.disable_buttons)
            self.window['-STOP MEASURE-'].update(disabled=False)
            ## 0. Exit loop
            if event in (WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT, None):
                break
            if vis.checkEscapeKey():
                break
            
            ## Event handler ##
            ## 1. XYZ control
            if event in ('<XY>', '<Z>', 'Go To', 'Reset'):
                self.update_position = True
            ### 1.1 Home
            if event in ('<XY>', '<Z>'):
                stage.home()
            ### 1.2 XYZ buttons
            if event in movement_buttons.keys():
                axis, displacement = movement_buttons[event]
                stage.move(axis, float(displacement))
                self.update_position = True
            ### 1.3 Go To Position
            if event == 'Go To':
                x = float(values['-X-CURRENT-'])
                y = float(values['-Y-CURRENT-'])
                z = float(values['-Z-CURRENT-'])
                stage.moveTo((x,y,z))
            if self.update_position:
                self.window['-X-CURRENT-'].update(stage.current_x)
                self.window['-Y-CURRENT-'].update(stage.current_y)
                self.window['-Z-CURRENT-'].update(stage.current_z)
                self.update_position = False

            ## 2. Macro buttons
            if event in ('-CAPTURE-', 'Measure'):
                today = date.today().strftime("%Y-%m-%d")
                savefolder = values['-SAVE FOLDER-']
                saveid = values['-SAMPLE ID-']
                savepath = f'{savefolder}/{today}/OUTPUT {saveid}'
                self.savepath = savepath
                if not os.path.exists(savepath):
                    os.makedirs(savepath)
                self.csvpath = f'{savepath}/positions_{saveid}.csv'
                self.imgpath = f'{savepath}/haarcascade_{saveid}.png'
                self.update_position = True
            if event in ('Default View', 'Probe', 'Cam'):
                self.update_position = True
            if event == 'Default View':
                self.default_view()
            if event == 'Set View':
                self.def_cam = (stage.current_x, stage.current_y)
                pop.notif('Set!')
            if event == 'Probe':
                self.switch('probe')
            if event == 'Cam':        
                self.switch('camera')
            if event == 'Calibrate':
                if stage.selected_position == 'camera':
                    self.calib_cam = (stage.current_x, stage.current_y)
                    recalib_cam = True
                    pop.notif('Set!')
                elif stage.selected_position == 'probe':
                    self.calib_probe = (stage.current_x, stage.current_y)
                    recalib_probe = True
                    pop.notif('Set!')
                if recalib_cam and recalib_probe:
                    offset_x = self.calib_probe[0] - self.calib_cam[0]
                    offset_y = self.calib_probe[1] - self.calib_cam[1]
                    self.probe_offset = (offset_x, offset_y)
                    recalib_cam, recalib_probe = False, False
            if event == '-CAPTURE-':
                vis.capture_image(self.frame_display, self.imgpath)
                pop.notif('Saved!')
            if event == '-EXIT-':
                break
            if event == '-SWITCHCTRL-':
                self.window[controls[curr_ctrl]].update(visible=False)
                curr_ctrl = (curr_ctrl+1)%len(controls)
                self.window[controls[curr_ctrl]].update(visible=True)
            
            ## 3. Measurements
            if event == 'Measure':
                if controls[curr_ctrl] == '-KEITHLEY-':
                    self.gate = None
                    self.gate = self.configure_Keithley(values['-G-ADDRESS-'], 'gate')
                    
                    pop.notif("Check connections! \nClick to start")
                    self.stop_measure = False
                    try:
                        thread = threading.Thread(target=self.measure_single, name=f'measure', daemon=False)
                        thread.start()
                        self.threads['measure'] = thread
                        # self.threads['measure'].join(timeout=60)
                    except:
                        pass
                elif controls[curr_ctrl] == '-HYSTERESIS-':
                    address = values['-SM-ADDRESS-']
                    current = float(values['-SM-CURR-'])
                    temp_values = np.arange(int(values['-TEMP-LO-']), int(values['-TEMP-HI-']), int(values['-TEMP-STEP-'])).tolist()
                    temp_values = temp_values[:-1] + sorted(temp_values, reverse=True)
                    temp_hold_time = int(values['-TEMP-HOLD-'])
                    temp_cool_time = int(values['-TEMP-COOL-'])
                    runs = int(values['-SM-RUNS'])
                    settings = [
                        '*RST',
                        'ROUT:TERM FRONT',

                        'SENS:FUNC "VOLT"',
                        'SENS:VOLT:RSEN ON',
                        'SENS:VOLT:RANG:AUTO ON',
                        'SENS:VOLT:NPLC 5',
                        'SENS:VOLT:UNIT OHM',
                        'SENS:VOLT:OCOM ON',

                        'SOUR:FUNC CURR',
                        'SOUR:CURR:RANG:AUTO ON',
                        'SOUR:CURR:VLIM 200',
                        #f'SENS:VOLT:RANG {voltmeter_range}',
                        f'SOUR:CURR {current}',
                        'OUTP ON',
                        ':syst:beep 440,1',
                    ]
                    self.gate = None
                    self.gate = self.configure_Keithley(address, 'gate', settings)
                    
                    pop.notif("Check connections! \nClick to start")
                    self.stop_measure = False
                    try:
                        args = [address, current, temp_values, temp_hold_time, temp_cool_time, runs]
                        thread = threading.Thread(target=self.measure_hysteresis, name=f'measure', daemon=False, args=args)
                        thread.start()
                        self.threads['measure'] = thread
                    except:
                        pass
            if event == '-STOP MEASURE-':
                self.stop_measure = True
                self.threads_active = False
                self.set_all_buttons(disable=False)
                pass
            if event == 'Set Temp':
                bed_temp = round( min(max(float(values["-BED TEMP-"]),0), 110) )
                try:
                    bed_temp = stage.heat(bed_temp)
                except:
                    bed_temp = None
                if bed_temp == None:
                    pop.notif('Unable to heat stage!')
                else:
                    pop.notif('Set!')
                self.window["-BED TEMP-"].update(bed_temp)

            ## 4. Vision control
            ret = False
            if not self.freeze_cam:
                ret, frame = vis.read_image()
                if controls[curr_ctrl] == '-HYSTERESIS-':
                    ret, frame = thermal.read_image(False) 
                pass
            ### 4.2 Process and detect target
            if ret:
                self.frame_display = frame
                self.display_current_image()

            ## 5. Keithley
            if event == 'Set Id-Vg':
                self.amp_range = (float(values['-G-START-']), float(values['-G-STOP-']), float(values['-G-STEP-']))
                self.window['-IDVG-G-'].update(value=f'Id-Vg, gate: {self.amp_range}')

        vis.close()
        return
    
    def average_data(self, data):
        """
        Adapted
        """
        result_x = []
        result_x_error = []
        result_y = []
        result_y_error = []

        temp_x = []
        temp_y = []

        for datapoint in data.values:
            temp_x.append(datapoint[1])
            temp_y.append(datapoint[2])
            if datapoint[0] == self.gate.numreadings-1:
                x_mean = np.average(temp_x)
                result_x.append(x_mean)
                result_x_error.append(np.std(temp_x))

                y_mean = np.average(temp_y)
                result_y.append(y_mean)
                result_y_error.append(np.std(temp_y))

                temp_x = []
                temp_y = []

        result = pd.DataFrame()
        result['Ig_average'] = result_x
        result['Vg_average'] = result_y
        result['Ig_error'] = result_x_error
        result['Vg_error'] = result_y_error
        #add in a filter to rule out clear errorus point
        result = result[result['Ig_average']<1]
        # add in another filter to get 05 quantile
        result = result[(result['Ig_average'] < np.percentile(result['Ig_average'],65))
                        & (result['Ig_average'] > np.percentile(result['Ig_average'],27))]
        return result

    def configure_Keithley(self, address, name='', settings=[]):
        """
        Establish connection with Keithley
        - address: (short) IP address of Keithley
        - name: name of Keithley
        - settings: settings to be applied

        Return: toolutils.Keithley object
        """
        if len(settings) == 0:
            settings = [
                '*RST',
                # 'sense:current:OCOM ON',
                'ROUT:TERM FRONT',

                'SOUR:FUNC CURR',
                'SOUR:CURR:RANG:AUTO ON',
                'SOUR:CURR:VLIM 200',
                
                'SENS:FUNC "VOLT"',
                'SENS:VOLT:RSENSE ON',
                # 'SENS:VOLT:RANG:AUTO ON',
                # 'SENS:VOLT:RANG:AUTO:REB ON',
                'SENS:VOLT:RANG 200',
                'SENS:VOLT:UNIT VOLT'
            ]
        keithley = Keithley(address, name)
        keithley.getI, keithley.getV = keithley.applySettings(settings, 'I', 3, 100)
        return keithley

    def log_data(self, current=1e-7):
        gate = self.gate
        buffer = []
        max_buffer_size = 10000
        while self.threads_active:
            if self.stop_measure:
                break
            if len(buffer) > max_buffer_size:
                break
            temp4 = self.thermal.get_spotmeter_temps([4])
            # temp4 = 25
            # gate.readData()
            voc = None
            gate.setParameters(['TRAC:TRIG "defbuffer1"', 'FETCH? "defbuffer1", READ'])
            while voc is None:
                try:
                    voc = gate.inst.read()
                except:
                    # voc = np.nan
                    pass
            row = (self.operation_tag, datetime.now().strftime('%H:%M:%S'), temp4[0], voc)
            buffer.append(row)
            time.sleep(1)
        
        cols = ['operation_tag', 'time', 'temperature', 'voltage']
        df = pd.DataFrame(buffer, columns=cols)
        # df = pd.concat([df, gate.buffer_df], axis=1)
        # df.rename(columns={'Vg': 'voltage', 'Ig': 'current'}, inplace=True)
        df['voltage'] = df['voltage'].astype(np.float64)
        df['resistance'] = df['voltage'] / current # df['current']
        self.buffer_df = df
        return self.buffer_df

    def measure_hysteresis(self, address, current, temp_values, temp_hold_time, temp_cool_time=300, runs=1):
        # settings = []
        # if mode == 'seebeck':
        #     settings = [
        #         '*RST',
        #         'ROUT:TERM FRONT',
        #         'SENS:FUNC "VOLT"',
        #         'SENS:VOLT:RSEN OFF',
        #         'SENS:VOLT:NPLC 5',
        #         'SOUR:FUNC CURR',
        #         'SOUR:CURR:RANG 1e-8',
        #         'SOUR:CURR:VLIM 200',
        #         'SENS:VOLT:RANG 0.02',
        #         ':syst:beep 350,1',
        #         'OUTP ON'
        #     ]
        # self.gate = None
        # self.gate = Keithley(address, 'gate')
        # self.gate.getI, self.gate.getV = self.gate.applySettings(settings, 'V', 5, 100)
        gate = self.gate

        self.disable_buttons = True
        for run in range(runs):
            if self.stop_measure:
                break
            print("================= Starting run number", run, "==================")
            print("Active threads : ", threading.activeCount())
            # Optional sleep to wait for cool down
            if run > 0:
                print(f"==== Waiting for cooldown: {temp_cool_time} s")
                for _ in range(temp_cool_time):
                    if self.stop_measure:
                        break
                    time.sleep(1)

            self.threads_active = True
            self.operation_tag = 'IDLE'
            thread = threading.Thread(target = self.log_data, name = "DataLogger", daemon = False, args=[current])
            thread.start()
            
            for i, temp in enumerate(temp_values):
                if self.stop_measure:
                    break
                self.operation_tag = f'HEATING_{str(i+1).rjust(2, "0")}_{temp}'
                #hh.set_temperature(temp)
                print(f"==== Heater Temp {i+1}: ", temp, "^C")
                print(f"==== Waiting for {temp_hold_time} s")
                for _ in range(temp_hold_time):
                    if self.stop_measure:
                        break
                    time.sleep(1)
                print("Done!")
                gate.setParameters([':syst:beep 262,1'])
            
            self.threads_active = False
            thread.join()
            self.operation_tag = 'IDLE'
            if not self.stop_measure:
                highest_run_number = 0
                filepath = f'{self.savepath}/hysteresis_run{str(highest_run_number).rjust(2, "0")}.csv'
                while os.path.exists(filepath):
                    highest_run_number += 1
                    filepath = f'{self.savepath}/hysteresis_run{str(highest_run_number).rjust(2, "0")}.csv'
                self.buffer_df.to_csv(filepath)
                
                # plt.scatter(self.buffer_df['temperature'], self.buffer_df['voltage'])
                filepath = f'{self.savepath}/hysteresis_run{str(highest_run_number).rjust(2, "0")}.png'
                # plt.savefig(filepath)
                # plt.show()
                
        # Play music
        gate.setParameters([
            'OUTP OFF',
            ':syst:beep 350,0.3; :syst:beep 392,0.3; :syst:beep 440,0.3; :syst:beep 262,1',
            ':syst:beep 350,0.3; :syst:beep 392,0.3; :syst:beep 440,0.3; :syst:beep 262,1'
        ])
        self.disable_buttons = False
        return

    def measure_single(self):
        """
        Measure a single sample
        - amps_low : lower bound of the current value. The default is 1e-6.
        - amps_high : higher bound of the current value. The default is 1e-5.
        - amps_step : step size. The default is 1e-6.
        - path : path to output folder (str)

        Return: pd.DataFrame (IV values)
        """
        gate = self.gate
        amp_start, amp_stop, amp_step = self.amp_range
        if amp_start > 1 or amp_stop > 1:
            raise ValueError('current set too high, try lower values')
        if amp_step >= amp_stop:
            raise ValueError('current step is too big, try smaller step value')

        #Input measurement range
        curr = np.arange(*self.amp_range).tolist()
        print("Starting measurement")
        # gate.setParameters(['SENS:VOLT:AZER ON'])

        self.disable_buttons = True
        for c in curr:
            if self.stop_measure:
                break
            params = [
                f'SOUR:CURR {c}',
                f'trace:clear "{gate.name}data"',
                'output ON',
                f'trace:trigger "{gate.name}data"'
            ]
            gate.setParameters(params)
            gate.readData()
        gate.inst.write('OUTP OFF')
        highest_run_number = 0
        filepath = f'{self.savepath}/4pp_run{str(highest_run_number).rjust(2, "0")}.csv'
        while os.path.exists(filepath):
            highest_run_number += 1
            filepath = f'{self.savepath}/4pp_run{str(highest_run_number).rjust(2, "0")}.csv'
        gate.buffer_df.to_csv(filepath)
        # gate.buffer_df.to_csv(f'{self.savepath}/1.csv')

        # average_df = gate.buffer_df.copy()
        # average_df = self.average_data(average_df)
        # average_df.to_csv(f'{self.savepath}/av1.csv')
        self.disable_buttons = False
        print('Done!')
        self.platform.move('Z', float('+11'))
        return
    
    def fit_IV(self):
        """line 230"""
        return


# %%
