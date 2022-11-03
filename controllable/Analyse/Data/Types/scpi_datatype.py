# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""

class SCPI(object):
    """
    SCPI input class for Keithley.
    
    Args:
        string (str): text string of SCPI commands or filename of txt file where SCPI commands are saved
        scpi_list (list): list of SCPI commands line-by-line
    """
    def __init__(self, string='', scpi_list=[]):
        if len(string) == 0 and len(scpi_list):
            scpi_join = ['\n'.join(s) for s in scpi_list]
            string = '\n###\n'.join(scpi_join)
        elif string.endswith('.txt'):
            with open(string) as file:
                string = file.read()
        if len(string) == 0:
            raise Exception('Please input either filename or SCPI instruction string/list!')
        self.string = string
        return

    def replace(self, inplace=False, **kwargs):
        """
        Replace placeholder text in SCPI commands with desired values.
        
        Args:
            inplace (bool): whether to replace text in place
        
        Retruns:
            str: SCPI commands with desired values
        """
        string = self.string
        for k,v in kwargs.items():
            if type(v) == bool:
                v = 'ON' if v else 'OFF'
            string = string.replace(f'<{k}>', str(v))
        if inplace:
            self.string = string
            return
        return string

    def parse(self):
        """
        Parse SCPI command into blocks corresponding to settings prompt, input prompt, and output prompt.
        
        Returns:
            list: SCPI prompts for settings, inputs, and outputs
        """
        scpi_split = self.string.split('###')
        for i,s in enumerate(scpi_split):
            scpi_split[i] = [l.strip() for l in s.split('\n') if len(l)]
        if len(scpi_split) == 1:
            scpi_split = scpi_split[0]
        return scpi_split
