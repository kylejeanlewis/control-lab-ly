# %% -*- coding: utf-8 -*-
"""
Created on Thu 2022 Jul 28 12:40:00

@author: cjleong
"""
import os
import json
import time
import math
import numpy as np
import pandas as pd

from PySimpleGUI import WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT

import sys
here = os.getcwd()
there_dobot = here.split('src')[0] + 'src\\robotics\\dobot'
sys.path.append(there_dobot)
from guibuilder import Builder, Popups
import dobot_utils
print(f"Import: OK <{__name__}>")

PRELIM_CALIB = (194,31,0)
REF_POSITIONS = pd.read_excel(f'{there_dobot}\\settings\\Opentrons coordinates.xlsx', index_col=0).round(2).to_dict('index')
REF_POSITIONS = {k: tuple(v.values()) for k,v in REF_POSITIONS.items()}

LEFT = {
    'arm': dobot_utils.VacuumGrip,
    'details': {
        'address': '192.168.2.8',
        # 'home_position': '',
        # 'home_orientation': '',
        'orientate_matrix': np.array([[0,-1,0],[1,0,0],[0,0,1]]),
        'translate_vector': np.array([343.6,-57.9,-222.5]) * (-1) + np.array(PRELIM_CALIB),
        'scale': 1
    }
}

RIGHT = {
    'arm': dobot_utils.JawGripper,
    'details': {
        'address': '192.168.2.7',
        # 'home_position': '',
        # 'home_orientation': '',
        'orientate_matrix': np.array([[-1,0,0],[0,-1,0],[0,0,1]]),
        'translate_vector': np.array([-175.6,-330.3,-222.5]) * (-1) + np.array(PRELIM_CALIB),
        'scale': 1
    }
}

# %%
class Setup(object):
    def __init__(self):
        try:
            settings = self.loadSettings(filename='dobot_settings.json')
            left_arm = settings['left']
            right_arm = settings['right']
            pass
        except Exception as e:
            print(e)
            left_arm = LEFT
            right_arm = RIGHT

        self.Lobot = left_arm['arm'](**left_arm['details'])
        self.Robot = right_arm['arm'](**right_arm['details'])
        self.Lobot.calibrationMode()

        self.window = None
        self.update_position = True
        return

    # Main methods (build_window, gui_loop, run_program)
    def build_window(self):
        """
        Build GUI window from blocks provided in guibuilder.Builder object
        """
        bd = Builder()
        bd.addLayout('-FINAL-', [
            [bd.getB('LEFT', key='-SWITCH-ARM-'), bd.getB('RESET', key='-RESET-ARM-'), bd.getB('CALIBRATE', key='-CALIB-ARM-')],
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
        arms = [('LEFT', self.Lobot), ('RIGHT', self.Robot)]
        arm_id = 0
        arm = arms[arm_id][1]

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
                label, arm = arms[(arm_id)%len(arms)]
                self.window['-SWITCH-ARM-'].update(label)
                self.update_position = True
            ### 2.2 Reset arms
            if event == '-RESET-ARM-':
                arm.reset()
            ### 2.3 Reset arms
            # if event == '-CALIB-ARM-':
            #     self.calibrate(arm)
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
        # try:
        #     savefolder = paths['savefolder']
        # except:
        #     savefolder = ''
        # self.savefolder = savefolder
        # if len(self.savefolder) == 0:
        #     self.savefolder = os.getcwd().replace('\\', '/')
        # elif not os.path.exists(self.savefolder):
        #     os.makedirs(self.savefolder)
        
        self.build_window()
        self.window.Finalize()
        if maximize:
            self.window.Maximize()
        self.window.bring_to_front()
        self.gui_loop(paths)
        self.window.close()
        self.update_position = True
        return

    # Other methods
    def calibrate(self, arm):
        ref_pos_1 = int(input("Input reference position 1:"))
        space_pt_1 = np.array(REF_POSITIONS[ref_pos_1])
        arm.moveTo( tuple(np.append(space_pt_1[:2],30)) )
        self.run_program()
        robot_pt_1 = np.array(arm.getWorkspacePosition())

        ref_pos_2 = int(input("Input reference position 2:"))
        space_pt_2 = np.array(REF_POSITIONS[ref_pos_2])
        arm.moveTo( tuple(np.append(space_pt_2[:2],30)) )
        self.run_program()
        robot_pt_2 = np.array(arm.getWorkspacePosition())

        space_vector = space_pt_2 - space_pt_1
        robot_vector = robot_pt_2 - robot_pt_1
        space_mag = np.linalg.norm(space_vector)
        robot_mag = np.linalg.norm(robot_vector)

        space_unit_vector = space_vector / space_mag
        robot_unit_vector = robot_vector / robot_mag
        dot_product = np.dot(robot_unit_vector, space_unit_vector)
        cross_product = np.cross(robot_unit_vector, space_unit_vector)

        cos_theta = dot_product
        sin_theta = math.copysign(np.linalg.norm(cross_product), cross_product[2])
        rot_angle = math.acos(cos_theta) if sin_theta>0 else 2*math.pi - math.acos(cos_theta)

        rot_matrix = np.array([[cos_theta,-sin_theta,0],[sin_theta,cos_theta,0],[0,0,1]])
        arm.orientate_matrix = np.matmul(rot_matrix, arm.orientate_matrix)
        arm.translate_vector = arm.translate_vector + (space_pt_1 - robot_pt_1)
        arm.scale = (space_mag / robot_mag) * arm.scale
        
        print(f'Address: {arm.address}')
        print(f'Rotation matrix:\n{arm.orientate_matrix}')
        print(f'Translate vector: {arm.translate_vector}')
        print(f'Scale factor: {arm.scale}')
        print(f'Offset angle: {rot_angle/math.pi*180} degree')
        print(f'Offset vector: {(space_pt_1 - robot_pt_1)}')
        return

    def decodeSetting(self, setting):
        dobot_type = setting['arm']
        setting['arm'] = dobot_utils.__dict__[dobot_type]

        details = setting['details']
        setting['details'] = dobot_utils.decodeDetails(details)
        return setting

    def home(self):
        self.Lobot.home()
        self.Robot.home()
        return

    def loadSettings(self, filename='dobot_settings.json', location=there_dobot+'\\settings'):
        with open(f'{location}\\{filename}') as json_file:
            settings = json.load(json_file)
        for k,v in settings.items():
            settings[k] = self.decodeSetting(v)
        # print(settings)
        return settings

    def saveSettings(self, filename='dobot_settings.json', location=there_dobot+'\\settings'):
        settings = {"left": self.Lobot.getSettings(), "right": self.Robot.getSettings()}
        with open(f'{location}\\{filename}', 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        # print(f'{location}\\{filename}')
        return


# %%
if __name__ == '__main__':
    setup = Setup()
    setup.run_program()
    # setup.calibrate(setup.Lobot)
    # setup.calibrate(setup.Robot)

# %%
