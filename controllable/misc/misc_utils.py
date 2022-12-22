# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import os
import time

# Third party imports
import serial.tools.list_ports # pip install pyserial

# Local application imports
print(f"Import: OK <{__name__}>")

class Helper(object):
    """
    Helper class with miscellaneous methods
    """
    def __init__(self):
        self.all_logs = []
        self.logs = {}
        pass
    
    def display_ports(self):
        """
        Displays available ports

        Returns:
            list: list of connected serial ports
        """
        com_ports = []
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            com_ports.append(str(port))
            print(f"{port}: {desc} [{hwid}]")
        if len(ports) == 0:
            print("No ports detected!")
            return ['']
        return com_ports
    
    def log_now(self, message:str, group=None):
        """
        Add log with timestamp

        Args:
            message (str): message to be logged
            group (str, optional): message group. Defaults to None.

        Returns:
            str: log message with timestamp
        """
        log = time.strftime("%H:%M:%S", time.localtime()) + ' >> ' + message
        self.all_logs.append(log)
        if group:
            if group not in self.logs.keys():
                self.logs[group] = []
            self.logs[group].append(message)
        return log
    
    def pretty_print_duration(self, total_time:float):
        """
        Display time duration (s) as HH:MM:SS text

        Args:
            total_time (float): duration in seconds

        Returns:
            str: formatted time string
        """
        m, s = divmod(total_time, 60)
        h, m = divmod(m, 60)
        return f'{int(h)}hr {int(m)}min {int(s):02}sec'

    def reset_logs(self):
        """
        Reset all logs
        """
        self.all_logs = []
        self.logs = {}
        return

    def save_logs(self, groups=[], folder=''):
        """
        Write logs into txt files

        Args:
            groups (list, optional): list of log messages. Defaults to [].
            folder (str, optional): folder to save to. Defaults to ''.
        """
        dst_folder = '/'.join([folder, 'logs'])
        if not os.path.exists(dst_folder):
            os.makedirs(dst_folder)
        
        with open(f'{dst_folder}/activity_log.txt', 'w') as f:
            for line in self.all_logs:
                f.write(line + '\n')
        
        for group in groups:
            if group not in self.logs.keys():
                print(f"'{group}' not found in log groups!")
                continue
            with open(f'{dst_folder}/{group}_log.txt', 'w') as f:
                for line in self.logs[group]:
                    f.write(line + '\n')
        return
