# -*- coding: utf-8 -*-
""" 
This module contains classes for sending notifications.

Attributes:
    FILENAME_TIME_FORMAT (str): time format for filenames
    
## Classes:
    `Notifier`: class for sending notifications
    `EmailNotifier`: class for sending email notifications

<i>Documentation last updated: 2025-06-11</i>
"""
# Standard library imports
from __future__ import annotations
import base64
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
import smtplib
from typing import Any, Iterable

# Local application imports
from . import file_handler

FILENAME_TIME_FORMAT = '%Y%m%d_%H%M%S'

class Notifier:
    """ 
    `Notifier` class for sending notifications. Use the `Notifier` class as context manager to handle app passwords securely.
    
    ### Constructor:
        `configs` (dict): configuration details for the notifier
        
    ### Attributes and properties:
        `configs` (dict): configuration details for the notifier
        `decoder` (str): decoder for the app password
        `decoder_options` (list[str]): available decoder options
    
    ### Methods:
        `fromFile`: create a `Notifier` object from a configuration file
        `writeMessage`: write a message
        `notify`: write and send a message through chosen service
        `sendMessage`: send a message through chosen service
        `setDecoder`: set the decoder for the app password
    """
    
    def __init__(self, configs: dict):
        """ 
        Initialize `Notifier` class
        
        Args:
            configs (dict): configuration details for the notifier
        """
        assert 'credentials' in configs, "Credentials not found in configuration file"
        assert 'service' in configs, "Service details not found in configuration file"
        assert 'message' in configs, "Message details not found in configuration file"
        self.configs = configs
        self.decoder: str = 'base64'
        self._app_password: Path|None = None
        self._decoder_functions: dict[str, function[str|bytes, str]] = dict(
            base64 = lambda x: base64.b64decode(x).decode("ascii")
        )
        pass
    
    def __enter__(self):
        keyfile: Path = self.configs['credentials']['keyfile']
        while not keyfile.exists():
            keyfile = Path(input(f"Enter valid path to keyfile for {self.configs['credentials']['username']}: "))
        self._app_password = keyfile
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._app_password = None
        return
    
    @property
    def decoder_options(self) -> list[str]:
        """ 
        Get the available decoder options
        
        Returns:
            list[str]: list of available decoder options
        """
        return list(self._decoder_functions.keys())
    
    @classmethod
    def fromFile(cls, config_file: str|Path) -> Notifier:
        """ 
        Create a `Notifier` object from a configuration file
        
        Args:
            config_file (str|Path): Path to the configuration file
            
        Returns:
            Notifier: Notifier object created from the configuration file
        """
        config_file = Path(config_file)
        configs = file_handler.read_config_file(config_file)
        keyfile = str(configs['credentials']['keyfile'])
        configs['credentials']['keyfile'] = config_file.parent / keyfile.replace('~/', '')
        return cls(configs)
    
    @classmethod
    def writeMessage(cls, message_config: dict, placeholders: dict|None = None, *args, **kwargs) -> Any:
        """ 
        Write a message
        
        Args:
            message_config (dict): configuration details for the message
            placeholders (dict): placeholders for the message
            
        Returns:
            Any: message to be sent
        """
        ... # Replace with implementation
        raise NotImplementedError
    
    def notify(self, placeholders: dict|None = None, **kwargs):
        """ 
        Write and send a message through chosen service
        
        Args:
            placeholders (dict): placeholders for the message
        """
        placeholders = placeholders or dict()
        username = self.configs['credentials']['username']
        message = self.writeMessage(self.configs['message'], placeholders=placeholders, **kwargs)
        self.sendMessage(self.configs['service'], username, message)
        return
    
    def sendMessage(self, service_config: dict, username: str, message: Any):
        """ 
        Send a message through chosen service
        
        Args:
            service_config (dict): configuration details for the service
            username (str): username for the service
            message (Any): message to be sent
        """
        _app_password = self._app_password
        if _app_password is not None:
            assert isinstance(_app_password, (bytes,Path)), "App password not found"
        if isinstance(_app_password, Path):
            _app_password = self._app_password.read_bytes().strip()
        unencrypted_password = self._decoder_functions[self.decoder](_app_password)
        ... # Replace with implementation
        raise NotImplementedError
    
    def setDecoder(self, decoder: str, decoder_function: function|None = None):
        """ 
        Set the decoder for the app password
        
        Args:
            decoder (str): decoder to be used
        """
        if decoder_function is not None and callable(decoder_function):
            self._decoder_functions[decoder] = decoder_function
        assert decoder in self._decoder_functions, f"Decoder '{decoder}' not found"
        self.decoder = decoder
        return


class EmailNotifier(Notifier):
    """ 
    `EmailNotifier` class for sending email notifications. Use the `EmailNotifier` class as context manager to handle app passwords securely.
    
    ### Constructor:
        `configs` (dict): configuration details for the notifier
        
    ### Attributes and properties:
        `configs` (dict): configuration details for the notifier
        `decoder` (str): decoder for the app password
        `decoder_options` (list[str]): available decoder options
        
    ### Methods:
        `fromFile`: create a `Notifier` object from a configuration file
        `writeMessage`: write a message
        `writeEmail`: write an email message
        `notify`: write and send a message through chosen service
        `sendMessage`: send a message through chosen service
        `sendEmail`: send an email message through chosen server
        `setDecoder`: set the decoder for the app password
    """
    
    def __init__(self, configs: dict):
        super().__init__(configs)
        pass
    
    @classmethod
    def writeMessage(cls,message_config: dict, placeholders: dict|None = None, *args, **kwargs) -> EmailMessage:
        return cls.writeEmail(message_config, placeholders, *args, **kwargs)
    
    def sendMessage(self, service_config: dict, username: str, message: EmailMessage):
        return self.sendEmail(service_config=service_config, username=username, message=message)
    
    @classmethod
    def writeEmail(cls,
        message_config: dict, 
        placeholders: dict|None = None,
        *args,
        attachments: Iterable[Path]|None = None,
        save_zip: bool = False,
        time_format: str = '%Y-%m-%d %H:%M:%S',
        **kwargs
    ) -> EmailMessage:
        """
        Write an email message
        
        Args:
            message_config (dict): configuration details for the message
            placeholders (dict): placeholders for the message
            attachments (Iterable[Path]): filepaths of attachments to be sent
            save_zip (bool): whether to save the attachments as a zip file
            time_format (str): time format for the message
            
        Returns:
            `EmailMessage`: email message to be sent
        """
        placeholders = placeholders or dict()
        attachments = attachments or list()
        if 'timestamp' not in placeholders:
            placeholders['timestamp'] = datetime.now()
        placeholders_text, placeholders_file = placeholders.copy(), placeholders.copy()
        for key,value in placeholders.items():
            if isinstance(value, datetime):
                placeholders_text[key] = value.strftime(time_format)
                placeholders_file[key] = value.strftime(FILENAME_TIME_FORMAT)
        
        # Create email message
        msg = EmailMessage()
        for header,value in message_config['headers'].items():
            value: str = value
            if header in ('To','CC','BCC'):
                msg[header] = ', '.join(value)
                continue
            value = value.format(**placeholders_text)
            msg[header] = value
        content = message_config.get('content', '')
        content = content.format(**placeholders_text)
        msg.set_content(content)
        
        # Zip attachments
        attachment_name = message_config.get('attachment_name', "{timestamp}.zip")
        attachment_name = attachment_name.format(**placeholders_file)
        zip_filepath = file_handler.zip_files(attachments, attachment_name if save_zip else None)

        # Add attachment
        with open(zip_filepath, 'rb') as f:
            file_data = f.read()
        msg.add_attachment(file_data, maintype='text', subtype='plain', filename=attachment_name)
        
        # Remove temporary zip file
        if not save_zip:
            zip_filepath.unlink()
        return msg
    
    def sendEmail(self, service_config: dict, username: str, message: EmailMessage):
        """ 
        Send an email message through chosen server
        
        Args:
            service_config (dict): configuration details for the service
            username (str): username for the service
            message (EmailMessage): email message to be sent
        """
        _app_password = self._app_password
        if _app_password is not None:
            assert isinstance(_app_password, (bytes,Path)), "App password not found"
        if isinstance(_app_password, Path):
            _app_password = self._app_password.read_bytes().strip()
        unencrypted_password = self._decoder_functions[self.decoder](_app_password)
        
        # Email server connection
        with smtplib.SMTP(service_config['server'], service_config['port']) as server:
            if service_config['tls']:
                server.starttls()
            server.login(username, unencrypted_password)
            server.send_message(message)
        return
