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

# Local application imports
print(f"Import: OK <{__name__}>")

class Logger:
    """
    Logger class with miscellaneous methods
    """
    def __init__(self):
        self.all_logs = []
        self.logs = {}
        pass
    
    # Instance methods
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

LOGGER = Logger() 
"""NOTE: importing LOGGER gives the same instance of the 'Logger' class wherever you import it"""
