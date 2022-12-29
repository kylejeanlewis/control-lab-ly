# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
class SCPI(object):
    """
    SCPI input class for Keithley

    Args:
        data (str, or dict): dictionary of SCPI commands, or filename of txt file containing SCPI commands
    """
    def __init__(self, data):
        self.string = ''
        self._read_data(data)
        return
    
    def _read_data(self, data):
        """
        Read data

        Args:
            data (str, or dict): dictionary of SCPI commands, or filename of txt file containing SCPI commands

        Raises:
            Exception: Input type has to be str or dict
        """
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
            raise Exception('Please input either filename or SCPI instruction dict!')
        self.string = string
        return
    
    def getPrompts(self):
        """
        Get SCPI prompts

        Returns:
            dict: dictionary of SCPI prompts (settings, inputs, outputs)
        """
        sections = ['settings', 'inputs', 'outputs']
        scpi_dict = {}
        scpi_split = self.string.split('###')
        for i,s in enumerate(scpi_split):
            scpi_dict[sections[i]] = [l.strip() for l in s.split('\n') if len(l.strip())]
        return scpi_dict
    
    def replace(self, inplace=False, **kwargs):
        """
        Replace placeholder text in SCPI commands with desired values

        Args:
            inplace (bool, optional): whether to replace text in place. Defaults to False.
            **kwargs: additional keyword arguments to be replaced in SCPI prompt

        Returns:
            str: SCPI commands with desired values
        """
        string = self.string
        for k,v in kwargs.items():
            string = string.replace('{'+f'{k}'+'}', str(v)) if k in string else string
        # string = string.format(**kwargs)
        string = string.replace('True', 'ON')
        string = string.replace('False', 'OFF')
        if inplace:
            self.string = string
            return
        return string

# %%
