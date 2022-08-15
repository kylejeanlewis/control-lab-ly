# %%
# -*- coding: utf-8 -*-
"""
Created on Fri 2022/03/18 15:40:00

@author: Chang Jie
"""
import os, sys
import types

THERE = {'movement': 'utils\\movement', 'gui': 'utils\\gui', 'misc': 'utils\\misc'}
here = os.getcwd()
base = here.split('src')[0] + 'src'
there = {k: '\\'.join([base,v]) for k,v in THERE.items()}
for v in there.values():
    sys.path.append(v)

import setup
from cartesian_utils import Primitiv, Ender
from miscfunctions import display_ports
from guibuilder import Builder, Popups
print("Import: OK")

CUSTOM_GUI = False
MAXIMIZE_WINDOW = False
TOOLS = ['Movement', '4PP', 'FET']

tool = None
def main():
    global tool
    paths = {}
    pop = Popups()
    cwd = os.getcwd().replace('\\', '/')
    try:
        users = os.listdir(f'{cwd}/users')
    except:
        cwd = cwd + '/tools'
        users = os.listdir(f'{cwd}/users')
    user = pop.combo_plus_input(['[New]']+users, ['Pick a user:', 'Or create new:'], ['-USER-', '-NEW USER-'])
    
    platform = None
    platform_option = pop.combo(['Primitiv', 'Ender'], 'Pick a platform:', '-PLATFORM-')
    if platform_option.lower() == 'primitiv':
        platform = Primitiv
    elif platform_option.lower() == 'ender':
        platform = Ender

    tool_option = pop.combo(TOOLS, 'Pick a tool:', '-TOOL-')
    if tool_option.lower() == 'movement':
        tool = setup.BasicMovement(platform)
    else:
        if tool_option.lower() == '4pp':
            tool = setup.FourPointProbe(
                platform_class=platform,
                z_updown=(-94,-104), 
                default_cam=(-54,-61), 
                probe_offset=(29.7,-47.6), 
                calib_unit=18.935)
        elif tool_option.lower() == 'fet':
            tool = setup.FieldEffectTransistor(
                platform_class=platform,
                z_updown=(-94,-104), 
                default_cam=(-54,-61), 
                probe_offset=(29.7,-47.6), 
                calib_unit=18.935)
        paths['savefolder'] = f'{cwd}/users/{user}/{tool_option}'

    display_ports()
    print("\nDisplaying GUI")
    print('-' * 50)
    if CUSTOM_GUI:
        # Replace default GUI with functions as defined below
        tool.build_window = types.MethodType(build_window, tool)
        tool.gui_loop = types.MethodType(gui_loop, tool)
    tool.run_program(paths, maximize=MAXIMIZE_WINDOW)
    return tool


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
    from PySimpleGUI import WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT
    while True:
        event, values = self.window.read(timeout=20)

        if event in ('Ok', WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT, None):
            break
    return


if __name__ == '__main__':
    main()

# %%
