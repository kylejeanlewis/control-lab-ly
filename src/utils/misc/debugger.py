# %%
# -*- coding: utf-8 -*-
"""
Created on Fri 2022/03/18 09:00:00

@author: Chang Jie
"""
class Debugger(object):
    """
    Debugger class to turn on and off debug output.
    """
    def __init__(self, show_logs=True):
        self.output = show_logs
    
    def show_print(self, value):
        """Show debug output"""
        if self.output:
            print(value)
            return
        return value
