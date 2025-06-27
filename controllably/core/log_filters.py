# -*- coding: utf-8 -*-
""" 
This module contains custom logging filters for controlling log levels
and filtering logs based on module names or application roots.

## Classes:
    `CustomLevelFilter`: A filter that allows setting different minimum logging levels for different modules on a specific handler.
    `AppFilter`: A filter that allows/blocks logs based on whether their logger name starts with a specified application root name.

<i>Documentation last updated: 2025-06-11</i>
"""
import logging
import sys

class CustomLevelFilter(logging.Filter):
    """
    A filter that allows setting different minimum logging levels
    for different modules on a specific handler.
    """
    _instance = None 
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, default_level_name: str = 'WARNING'):
        if not self._initialized:
            super().__init__()
            self._module_levels = {}
            self._default_level = logging.getLevelName(default_level_name.upper())
            self._initialized = True

    def setModuleLevel(self, module_name: str, level: int):
        """
        Sets the minimum level for a given module on this handler
        
        Args:
            module_name (str): Name of the module for which to set the level
            level (int): The logging level to set for this module
        """
        assert isinstance(module_name, str), "module_name must be a string."
        assert isinstance(level, int), "level must be a logging level (e.g., logging.DEBUG)."
        self._module_levels[module_name] = level
        return

    def getModuleLevel(self, module_name: str) -> int:
        """
        Gets the currently set level for a module or its parent, or default
        
        Args:
            module_name (str): Name of the module for which to get the level
            
        Returns:
            int: The logging level for the module, or the default level if not set
        """
        parts = module_name.split('.')
        # Check from most specific to least specific
        for i in range(len(parts), 0, -1):
            name_check = '.'.join(parts[:i])
            if name_check in self._module_levels:
                return self._module_levels[name_check]
        return self._default_level

    def clear(self):
        """Clears all custom module levels, reverting to default."""
        self._module_levels.clear()
        return

    def filter(self, record: logging.LogRecord) -> bool:
        required_level = self.getModuleLevel(record.name)
        return record.levelno >= required_level

class AppFilter(logging.Filter):
    """
    A filter that allows/blocks logs based on whether their logger name
    starts with a specified application root name.
    """
    def __init__(self, app_root_name: str, invert: bool = False):
        super().__init__()
        self.app_root_name = app_root_name
        self.invert = invert # If True, blocks app logs and allows others; if False, allows app logs and blocks others
    
    def __repr__(self):
        return f"<AppFilter app_root='{self.app_root_name}' invert={self.invert}>"
    
    def filter(self, record: logging.LogRecord) -> bool:
        is_app_log = record.name.startswith(self.app_root_name)
        return is_app_log if not self.invert else not is_app_log

# Configure the logging system
fmt = logging.Formatter("%(message)s")
custom_console_filter = CustomLevelFilter()
controllably_filter = AppFilter('controllably')

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(fmt)
stdout_handler.addFilter(controllably_filter)
stdout_handler.addFilter(custom_console_filter)

app_logger = logging.getLogger('controllably')
app_logger.setLevel(logging.DEBUG)
app_logger.addHandler(stdout_handler)
app_logger.propagate = False
print("NOTE: StreamHandler added to 'controllably' logger, which does not propagate to the root logger")
