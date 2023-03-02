# %% -*- coding: utf-8 -*-
"""
Class object to control the Tricontinent C-Series Syringe Pumps

Author: Aniket Chitre
Date: July 2022
"""
# Standard library imports
import time
from typing import Protocol

# Third party imports
import serial # pip install pyserial

# Local application imports
from .pump_utils import Pump
print(f"Import: OK <{__name__}>")

class C3000(Pump):
    def __init__(self, port: str, verbose=False):
        super().__init__(port, verbose)
    
    def _query(self, string:str, timeout_s=READ_TIMEOUT_S, resume_feedback=False):
        """
        Send query and wait for response

        Args:
            string (str): message string
            timeout_s (int, optional): duration to wait before timeout. Defaults to READ_TIMEOUT_S.

        Returns:
            str: message readout
        """
        start_time = time.time()
        message_code = self._write(string)
        response = ''
        while not self._is_expected_reply(message_code, response):
            if time.time() - start_time > timeout_s:
                break
            response = self._read()
        # print(time.time() - start_time)
        if message_code in QUERIES:
            response = response[2:]
        if message_code not in STATUS_QUERIES and resume_feedback:
            self.setFlag('pause_feedback', False)
        return response

    def _read(self):
        """
        Read response from device

        Returns:
            str: response string
        """
        response = ''
        try:
            response = self.device.readline()
            if len(response) == 0:
                response = self.device.readline()
            response = response[2:-2].decode('utf-8')
            if response in ERRORS:
                print(ErrorCode[response].value)
                return response
            elif response == 'ok':
                return response
        except Exception as e:
            if self.verbose:
                print(e)
        return response
    
    def _write(self, string:str):
        """
        Sends message to device

        Args:
            string (str): <message code><value>

        Returns:
            str: two-character message code
        """
        message_code = string[:2]
        fstring = f'/{self.channel}{string}\r' # message template: <PRE><ADR><CODE><DATA><LRC><POST>
        bstring = fstring.encode('utf-8')
        try:
            # Typical timeout wait is 400ms
            self.device.write(bstring)
        except Exception as e:
            if self.verbose:
                print(e)
        return message_code
    
    def prime(self):
        return
    def dose(self):
        return
    
    @property
    def position(self):
        response = self._query('?')
        return