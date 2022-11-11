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
        scpi_list (list): list of SCPI prompts for settings, inputs, and outputs
    """
    def __init__(self, data):
        self.string = ''
        self._read_data(data)
        return
    
    def _read_data(self, data):
        string = ''
        if type(data) == dict:
            for k,v in data.items():
                data[k] = '\n'.join(v)
            string = '\n###\n'.join([data['settings'], data['inputs'], data['outputs']])
        elif type(data) == str:
            if 'data'.endswith('.txt'):
                with open(data) as file:
                    data = file.read()
            string = data
        else:
            raise Exception('Please input either filename or SCPI instruction string/list!')
        self.string = string
        return
    
    def getPrompts(self):
        """
        Parse SCPI command into blocks corresponding to settings prompt, input prompt, and output prompt.
        
        Returns:
            dict: SCPI prompts for settings, inputs, and outputs
        """
        sections = ['settings', 'inputs', 'outputs']
        scpi_dict = {}
        scpi_split = self.string.split('###')
        for i,s in enumerate(scpi_split):
            scpi_dict[sections[i]] = [l.strip() for l in s.split('\n') if len(l)]
        return scpi_dict
    
    def replace(self, inplace=False, **kwargs):
        """
        Replace placeholder text in SCPI commands with desired values.
        
        Args:
            inplace (bool): whether to replace text in place
        
        Retruns:
            str: SCPI commands with desired values
        """
        string = self.string
        string = string.format(**kwargs)
        string = string.replace('True', 'ON')
        string = string.replace('False', 'OFF')
        if inplace:
            self.string = string
            return
        return string

# %%
