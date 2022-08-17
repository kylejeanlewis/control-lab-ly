# %% -*- coding: utf-8 -*-
"""
Created on Thu 2022 Jul 28 12:40:00

@author: cjleong

Notes:
Issues faced when calibrating points, such as 
1) decimal precision during matrix math;
2) CAD deck model slightly different from physical measurments -- > use calipers to measure;
2) deck not being level --> use spirit bubble to level arm and deck;
3) precision of eyeballing crosshairs / blunt tip --> use laser crosshair for calibration

~GUI does not show actual position after reset~
"""
import os, sys
import json
import numpy as np
import pandas as pd

from PySimpleGUI import WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT

THERE = {'movement': 'utils\\movement', 'dobot': 'utils\\movement\\dobot', 'gui': 'utils\\gui'}
here = os.getcwd()
base = here.split('src')[0] + 'src'
there = {k: '\\'.join([base,v]) for k,v in THERE.items()}
for v in there.values():
    sys.path.append(v)

import dobot_utils
from guibuilder import Builder
print(f"Import: OK <{__name__}>")

CONFIG_JSON = "config/dobot_settings L3.json"
REF_POSITIONS = pd.read_excel("config/Opentrons coordinates.xlsx", index_col=0).round(2).to_dict('index')
REF_POSITIONS = {k: tuple(v.values()) for k,v in REF_POSITIONS.items()}
CALIB_POINTS = 2

# %%
class Setup(object):
    def __init__(self, config_filename=CONFIG_JSON):
        self.filename = config_filename
        self.arms = {}
        self.arms_index = []
        try:
            self.loadSettings(config_filename)
            pass
        except Exception as e:
            print(e)

        self.window = None
        self.update_position = True
        self.begin_calibrate = None
        self.prev_position = (0,0,0)
        return

    # Main methods (build_window, gui_loop, run_program)
    def build_window(self):
        """
        Build GUI window from blocks provided in guibuilder.Builder object
        """
        bd = Builder()
        bd.addLayout('-FINAL-', [
            [bd.getB(self.arms_index[0], key='-SWITCH-ARM-'), bd.getB('RESET', key='-RESET-ARM-'), bd.getB('CALIBRATE', key='-CALIB-ARM-')],
            [bd.getB('Grab', key='-ARM-GRAB-'), bd.getB('Release', key='-ARM-RELEASE-')],
            [bd.getXYZControls()],
            [bd.getTitle("", (64,1))],
            [bd.getPositions()]
            ], alignV='top')
        self.window = bd.getWindow("XYZ-arm controls")
        return

    def gui_loop(self, paths={}):
        """
        Run a loop to keep GUI window open
        - paths: dict of paths to save output
        """
        arm_id = 0
        arm = self.arms[self.arms_index[arm_id]]
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
                arm.home()
            ### 1.2 XYZ buttons
            if event in movement_buttons.keys():
                axis, displacement = movement_buttons[event]
                displacement = float(displacement)
                vector = [0,0,0]
                vector[['X', 'Y', 'Z'].index(axis)] = displacement
                vector = tuple(vector)
                arm.moveBy(vector)
                self.update_position = True
            ### 1.3 Go To Position
            if event == 'Go To':
                try:
                    x = float(values['-X-CURRENT-'])
                    y = float(values['-Y-CURRENT-'])
                    z = float(values['-Z-CURRENT-'])
                except ValueError:
                    print('Input float only!')
                arm.moveTo((x,y,z))
            if self.update_position:
                # Read last known position
                x = float(values['-X-CURRENT-'])
                y = float(values['-Y-CURRENT-'])
                z = float(values['-Z-CURRENT-'])
                self.prev_position = (x,y,z)
                # Get arm position
                workspace_coord = arm.getWorkspacePosition()
                workspace_coord = tuple([round(wc,2) for wc in workspace_coord])
                self.window['-X-CURRENT-'].update(workspace_coord[0])
                self.window['-Y-CURRENT-'].update(workspace_coord[1])
                self.window['-Z-CURRENT-'].update(workspace_coord[2])
                self.update_position = False
            
            ## 2. Arm actions
            ### 2.1 Switch arms
            if event == '-SWITCH-ARM-':
                arm_id += 1
                label = self.arms_index[arm_id%len(self.arms_index)]
                arm = self.arms[label]
                self.window['-SWITCH-ARM-'].update(label)
                self.update_position = True
            ### 2.2 Reset arms
            if event == '-RESET-ARM-':
                arm.reset()
                arm.setPosition(self.prev_position)
                self.update_position = True
            ### 2.3 Calibrate arms
            if event == '-CALIB-ARM-':
                self.begin_calibrate = arm
                break
            ### 2.4 Grab object
            if event == '-ARM-GRAB-':
                try:
                    arm.grab()
                except AttributeError as e:
                    print(e)
            ### 2.5 Release object
            if event == '-ARM-RELEASE-':
                try:
                    arm.release()
                except AttributeError as e:
                    print(e)
        return

    def run_program(self, paths={}, maximize=False):
        """
        Run program based on build_window and defined gui_loop
        - paths: dict of paths to save output
        - maximize: whether to maximize window
        """
        self.build_window()
        self.window.Finalize()
        if maximize:
            self.window.Maximize()
        self.window.bring_to_front()
        self.gui_loop(paths)
        self.window.close()
        self.update_position = True
        if type(self.begin_calibrate) != type(None):
            return self.calibrate(self.begin_calibrate)
        return

    # Other methods
    def calibrate(self, arm):
        arm.calibrationMode(True)
        self.begin_calibrate = None
        positions = []
        for p in range(1,CALIB_POINTS+1):
            ref_pos = int(input(f"Input reference position {p}:"))
            space_pt = np.array(REF_POSITIONS[ref_pos])
            positions.append(space_pt)
            arm.moveTo( tuple(np.append(space_pt[:2],30)) )
            self.run_program()
            robot_pt = np.array(arm.getWorkspacePosition())
            positions.append(robot_pt)
            arm.home()
        print(positions)
        arm.calibrate(*positions)
        arm.calibrationMode(False)
        return

    def decodeSetting(self, setting):
        dobot_type = setting['arm']
        details = setting['details']
        setting['arm'] = dobot_utils.__dict__[dobot_type]
        setting['details'] = dobot_utils.decodeDetails(details)
        return setting

    def getArm(self, name):
        this_arm = None
        try:
            this_arm = self.arms[name.upper()]
        except:
            print("Arm not found!")
        return this_arm

    def home(self):
        for _, arm in self.arms.items():
            arm.home()
        return

    def loadSettings(self, filename=''):
        if len(filename) == 0:
            filename = self.filename
        with open(filename) as json_file:
            settings = json.load(json_file)
        for k,v in settings.items():
            setting = self.decodeSetting(v)
            self.arms[k.upper()] = setting['arm'](**setting['details'])
            self.arms_index.append(k.upper())
        return settings

    def saveSettings(self, filename=''):
        if len(filename) == 0:
            filename = self.filename
        settings = {name.lower(): arm.getSettings() for name,arm in self.arms}
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        print(f'Saved to {filename} !')
        return


# %%
if __name__ == '__main__':
    if 'setup' not in dir():
        setup = Setup()
    setup.run_program()

# %%
