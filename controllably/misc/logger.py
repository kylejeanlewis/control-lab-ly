# %% -*- coding: utf-8 -*-
"""
This module holds the logger class in Control.lab.ly.

Classes:
    Logger

Other constants and variables:
    LOGGER (Logger)
"""
# Standard library imports
import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

class _Logger:
    """
    Logger class with miscellaneous methods
    
    ### Constructor
    Args:
        `name` (str): name of logger
    
    ### Attributes
    - `all_logs` (list[str]): list of all logs
    - `logs` (dict): logs by group
    - `name` (str): name of logger
    
    ### Methods
    - `log_now`: add log message with timestamp
    - `reset_logs`: clear past logs
    - `save_logs`: save logs to file
    """
    
    def __init__(self, name:str):
        """
        Instantiate the class

        Args:
            name (str): name of logger
        """
        self.name = name
        self.all_logs = []
        self.logs = {}
        pass
    
    def log_now(self, message:str, group:Optional[str] = None) -> str:
        """
        Add log message with timestamp

        Args:
            message (str): message to be logged
            group (Optional[list], optional): message group. Defaults to None.

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
        """Clear past logs"""
        self.all_logs = []
        self.logs = {}
        return

    def save_logs(self, groups:Optional[list] = None, folder:str = ''):
        """
        Save logs to file

        Args:
            groups (Optional[list], optional): list of log messages. Defaults to None.
            folder (str, optional): folder to save to. Defaults to ''.
        """
        groups = [] if groups is None else groups
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

LOGGER = _Logger('main') 
"""NOTE: importing LOGGER gives the same instance of the 'Logger' class wherever you import it"""

def main():
    # logging.basicConfig(
    #     level=logging.DEBUG,
    #     format="%(asctime)s %(levelname)s %(message)s",
    #     datefmt="%Y-%m-%d %H:%M:%S",
    #     filename="basic.log",
    #     filemode='a'
    # )
    
    logger.debug("This is a debug message.")
    logger.info("This is a info message.")
    logger.warning("This is a warning message.")
    logger.error("This is a error message.")
    logger.critical("This is a critical message.")
    
    # handler = logging.FileHandler("test.log")
    # formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    # handler.setFormatter(formatter)
    # logger.addHandler(handler)
    
    # logger.info("test custom logger")

if __name__ == '__main__':
    main()

# %%
