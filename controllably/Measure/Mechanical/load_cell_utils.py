# %% -*- coding: utf-8 -*-
"""

"""
# Standard library imports
from datetime import datetime
import pandas as pd
from threading import Thread
import time

# Local application imports
from ..measure_utils import Measurer
print(f"Import: OK <{__name__}>")

COLUMNS = ('Time', 'Value')
"""Headers for output data from load cell"""

class LoadCell(Measurer):
    def __init__(self, verbose: bool = False, **kwargs):
        super().__init__(verbose, **kwargs)
        self.baseline = 0
        self.buffer_df = pd.DataFrame(columns=COLUMNS)
        self.calibration_factor = 1
        self.precision = 3
        self._threads = {}
        return
    
    def clearCache(self):
        """Clear most recent data and configurations"""
        self.setFlag(pause_feedback=True)
        time.sleep(0.1)
        self.buffer_df = pd.DataFrame(columns=COLUMNS)
        self.setFlag(pause_feedback=False)
        return
    
    def disconnect(self):
        """Disconnect from device"""
    
    def getValue(self) -> str:
        """
        Get the value of the force response on the load cell
        
        Returns:
            str: device response
        """
        response = self._read()
        now = datetime.now()
        try:
            value = int(response)
        except ValueError:
            pass
        else:
            if self.flags['record']:
                values = [
                    now, 
                    value
                ]
                row = {k:v for k,v in zip(COLUMNS, values)}
                new_row_df = pd.DataFrame(row, index=[0])
                self.buffer_df = pd.concat([self.buffer_df, new_row_df], ignore_index=True)
        return response
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.toggleFeedbackLoop(on=False)
        return super().shutdown()
    
    def toggleFeedbackLoop(self, on:bool):
        """
        Start or stop feedback loop

        Args:
            on (bool): whether to start loop to continuously read from device
        """
        self.setFlag(get_feedback=on)
        if on:
            if 'feedback_loop' in self._threads:
                self._threads['feedback_loop'].join()
            thread = Thread(target=self._loop_feedback)
            thread.start()
            self._threads['feedback_loop'] = thread
        else:
            self._threads['feedback_loop'].join()
        return
    
    def toggleRecord(self, on:bool):
        """
        Start or stop data recording

        Args:
            on (bool): whether to start recording data
        """
        self.setFlag(record=on, get_feedback=on, pause_feedback=False)
        self.toggleFeedbackLoop(on=on)
        return
    
    # Protected method(s)
    def _connect(self, *args, **kwargs):
        """
        Connection procedure for tool
        """
        return super()._connect(*args, **kwargs)

    def _loop_feedback(self):
        """Loop to constantly read from device"""
        print('Listening...')
        while self.flags['get_feedback']:
            if self.flags['pause_feedback']:
                continue
            self.getValue()
        print('Stop listening...')
        return
    
    def _read(self) -> str:
        """
        Read response from device

        Returns:
            str: response string
        """
        return ''
    
    def _stream_data(self):
        volt = self.device._query("MEASure:VOLTage?")
        

