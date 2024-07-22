# %%
from __future__ import annotations
from abc import ABC, abstractmethod
import keyboard
import logging
import nest_asyncio
import numpy as np
import os
from threading import Thread
from typing import Optional, Union, Any, Protocol
import webbrowser

from nicegui import ui, app
from nicegui.elements.button import Button
from nicegui.elements.dialog import Dialog
from nicegui.events import UiEventArguments

nest_asyncio.apply()

logger = logging.getLogger(__name__)
panels: list[Panel] = []

class Mover(Protocol):
    _place: str
    heights: dict
    home_coordinates: tuple
    tool_position: tuple[np.ndarray]
    def home(self, *args, **kwargs):
        ...
    def move(self, *args, **kwargs):
        ...
    def moveTo(self, *args, **kwargs):
        ...
    def reset(self, *args, **kwargs):
        ...
    def rotateTo(self, *args, **kwargs):
        ...
    def safeMoveTo(self, *args, **kwargs):
        ...
    def _transform_out(self, *args, **kwargs):
        ...

# %%
class Panel:#(ABC):
    """
    Abstract Base Class (ABC) for Panel objects (i.e. GUI panels).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.

    ### Constructor
    Args:
        `name` (str, optional): name of panel. Defaults to ''.
        `group` (Optional[str], optional): name of group. Defaults to None.
        `panels` (list[Panel], optional): list of sub-panels. Defaults to list().
    
    ### Attributes
    - `flags` (dict[str, bool]): keywords paired with boolean flags
    - `group` (str): name of group
    - `panels` (list[Panel]): list of sub-panels
    - `tool` (Callable): tool to be controlled
    - `values` (dict[str,Any]): values from user interface
    
    ### Properties
    - `host` (str): server host
    - `name` (str): name of panel
    - `page_address` (str): page route
    - `port` (int): server port
    - `root_address` (str): host and port of server
    
    ### Methods
    #### Abstract
    - `getLayout`: build `sg.Column` object
    - `listenEvents`: listen to events and act on values
    #### Public
    - `close`: close the browser tab
    - `configure`: configure GUI defaults
    - `getMultiPanel`: build multi-panel page
    - `getPage`: build GUI page
    - `getWindow`: get landing page window
    - `parseInput`: parse inputs from GUI
    - `redirect`: redirect to panel's page address
    - `runGUI`: run the GUI loop
    - `setFlag`: set flags by using keyword arguments
    - `shutdown`: exit the application
    """
    
    _default_flags: dict[str, bool] = dict(notify=True)
    _default_values: dict[str, Any] = dict()
    _shutdown_dialog: Dialog | None = None
    _thread: list[Thread] = []
    _used_names: list[str] = []
    def __init__(self, 
        name: str = '', 
        group: Optional[str] = None,
        panels: list[Panel] = list()
    ):
        """
        Instantiate the class

        Args:
            name (str, optional): name of panel. Defaults to ''.
            group (Optional[str], optional): name of group. Defaults to None.
            panels (list[Panel], optional): list of sub-panels. Defaults to list().
        """
        self._name = ''
        self.name = name
        self.group = group
        self.panels: list[Panel] = panels
        
        self.flags = self._default_flags.copy()
        self.tool = None
        self.values = self._default_values.copy()
        
        self._host = os.environ.get('NICEGUI_HOST', '0.0.0.0')
        self._port = int(os.environ.get('NICEGUI_PORT', '8080'))
        return
    
    def __del__(self):
        self.shutdown(force=True)
    
    # Properties
    @property
    def host(self) -> str:
        return '127.0.0.1' if self._host == '0.0.0.0' else self._host
    
    @property
    def name(self) -> str:
        return self._name
    @name.setter
    def name(self, value: str):
        if value in self._used_names:
            raise Exception('Named already used. Choose another name for GUI.')
        self._name = value
        self._used_names.append(value)
        return
    
    @property
    def page_address(self) -> str:
        return f'/{self.name}'
    
    @property
    def port(self) -> int:
        return self._port
    
    @property
    def root_address(self) -> str:
        return f'{self.host}:{self.port}'
    
    # @abstractmethod
    def getLayout(self):
        """Build the UI layout"""
        self.values.update(dict(
            checkbox=True,
            notify=False,
            radio='B',
            input='type here',
            select=None
        ))
        with ui.card():
            ui.markdown(f'## {self.name}')
            ui.button('Button', on_click=self.listenEvents)
            with ui.row():
                ui.checkbox('Checkbox', on_change=self.listenEvents).bind_value(self.values, 'checkbox')
                ui.switch('Switch', on_change=self.listenEvents).bind_value(self.flags, 'notify')
            ui.radio(['A', 'B', 'C'], value='A', on_change=self.listenEvents).props('inline').bind_value(self.values, 'radio')
            with ui.row():
                ui.input('Text input', on_change=self.listenEvents).bind_value(self.values, 'input')
                ui.select(['One', 'Two'], value='One', on_change=self.listenEvents).bind_value(self.values, 'select')
            ui.link('And many more...', '/documentation').classes('mt-8')
        return

    # @abstractmethod
    def listenEvents(self, ui_event: UiEventArguments) -> dict[str, Any]:
        """
        Listen to events and act on values

        Args:
            ui_event (UiEventArguments): event object from NiceGUI

        Returns:
            dict: dictionary of values
        """
        event = type(ui_event.sender).__name__
        if event.lower() == 'button':
            sender: Button = ui_event.sender
            value = sender.text
            self.values.update(dict(click=value))
        values = self.values
        
        ...
        return self._show_values(ui_event=ui_event)

    @classmethod
    def close(cls):
        """Close the browser tab"""
        try:
            cls._shutdown_dialog.close()
            keyboard.press_and_release('ctrl+w')
        except Exception as e:
            logger.exception(e)
        return

    @classmethod
    def configure(cls, **kwargs):
        """Configure GUI defaults"""
        ui.dark_mode(True)
        with ui.dialog() as dialog, ui.card():
            cls._shutdown_dialog = dialog
            ui.label('Once shutdown, kernel needs to be restarted to open the GUI server again.')
            with ui.row().classes('w-full justify-center'):
                ui.button('Cancel', on_click=cls._shutdown_dialog.close)
                ui.button('Close tab', on_click=cls.close)
                ui.button('Shutdown', on_click=lambda: cls.shutdown(True), color='negative')
        return

    def getMultiPanel(self):
        """Build multi-panel page"""
        @ui.page(self.page_address)
        async def get_multi_panel_page():
            """Build multi-panel page"""
            self.configure()
            with ui.row().classes('w-full justify-between items-center'):
                ui.markdown(f'# {self.name}')
                ui.button('✖', on_click=self._shutdown_dialog.open, color='negative')
                
            with ui.row().classes('w-full justify-center'):
                for panel in self.panels:
                    panel.getLayout()
                    panel.getPage()
            
            await ui.context.client.connected()
            logging.debug(f'Connected: {self.root_address}{self.page_address}')
            await ui.context.client.disconnected()
            logging.debug(f'Disconnected: {self.root_address}{self.page_address}')
            return
        return

    def getPage(self) -> str:
        """Build GUI page"""
        @ui.page(self.page_address)
        async def get_page():
            """Build GUI page"""
            self.configure()
            self.getLayout()
            ui.button('✖', on_click=self._shutdown_dialog.open, color='negative')
            
            await ui.context.client.connected()
            logging.debug(f'Connected: {self.root_address}{self.page_address}')
            await ui.context.client.disconnected()
            logging.debug(f'Disconnected: {self.root_address}{self.page_address}')
            return
        return self.page_address
    
    def getWindow(self):
        """"""
        global panels
        if len(self.panels):
            self.getMultiPanel()
        else:
            self.getPage()
        if self not in panels:
            panels.append(self)
        
        @ui.page('/')
        async def index():
            """Build landing page"""
            self.configure()
            with ui.row().classes('w-full justify-between items-center'):
                ui.markdown(f'# Control-lab-ly')
                ui.button('✖', on_click=self._shutdown_dialog.open, color='negative')
                
            with ui.tabs().classes('w-full') as ui_tabs:
                tabs = []
                default_tab = None
                for panel in panels:
                    tab = ui.tab(panel.name)
                    tabs.append(tab)
                    if panel.name == self.name:
                        default_tab = tab
                default_tab = tabs[-1] if default_tab is None else default_tab
            
            with ui.tab_panels(ui_tabs, value=default_tab).classes('w-full'):
                for tab,panel in zip(tabs, panels):
                    with ui.tab_panel(tab):
                        if len(panel.panels):
                            with ui.row().classes('w-full justify-center'):
                                for panel in panel.panels:
                                    panel.getLayout()
                        else:
                            panel.getLayout()
            return
        return

    @classmethod
    def parseInput(cls, text:str) -> Union[list, bool, float, str, None]:
        """
        Parse inputs from GUI

        Args:
            text (str): input text read from GUI window

        Returns:
            Union[list, bool, float, str, None]: variable output including floats, strings, and tuples
        """
        text = text.strip()
        if len(text) == 0:
            return None
        
        array = []
        if ',' in text:
            array = text.split(',')
        elif ';' in text:
            array = text.split(';')
        if len(array):
            new_array = []
            for value in array:
                new_array.append(cls.parseInput(value))
            return new_array
        
        if text.replace('.','',1).replace('-','',1).isdigit():
            if '.' in text:
                return float(text)
            else:
                return int(text)
        
        if text.title() == "True":
            return True
        if text.title() == "False":
            return False
        
        if text[0] in ("'", '"') and text[-1] in ("'", '"'):
            return text[1:-1]
        return text
    
    def redirect(self):
        """Redirect to panel's page address"""
        return ui.navigate.to(self.page_address)
    
    def runGUI(self, title:str = 'Control-lab-ly', **kwargs):
        """
        Run the GUI loop

        Args:
            title (str, optional): title of window. Defaults to 'Control-lab-ly'.
        """
        # self.configure()
        self.getWindow()
        if 'NICEGUI_HOST' in os.environ:
            webbrowser.open(f'http://{self.root_address}{self.page_address}')
        elif not len(self._thread):
            self._port = int(os.environ.get('NICEGUI_PORT', '8080'))
            kwargs.update(dict(title=title, reload=False, host=self.host, port=self.port, show=False))
            thread = Thread(target=ui.run, kwargs=kwargs)
            self._thread.append(thread)
            self._thread[0].start()
            webbrowser.open(f'http://{self.root_address}{self.page_address}')
        else:
            logger.error('Unable to run GUI.')
        return
    
    def setFlag(self, **kwargs):
        """
        Set flags by using keyword arguments

        Kwargs:
            key, value: (flag name, boolean) pairs
        """
        if not all([type(v)==bool for v in kwargs.values()]):
            raise ValueError("Ensure all assigned flag values are boolean.")
        self.flags.update(kwargs)
        for key, value in kwargs.items():
            self.flags[key] = value
        return

    @classmethod
    def shutdown(cls, force: bool = False):
        """Exit the application"""
        if not force:
            proceed = input('Once shut down, kernel needs to be restarted to open the GUI server again. Proceed? (y/n)')
            if proceed.strip().lower() != 'y':
                logger.warning('Abort closing GUI server.')
                return
        try:
            cls._shutdown_dialog.close()
            cls.close()
            app.shutdown()
        except Exception as e:
            logger.exception(e)
        return
    
    # Protected method(s)
    def _show_values(self, ui_event: UiEventArguments) -> dict[str, Any]:
        """
        Show the GUI values

        Args:
            ui_event (UiEventArguments): event object from NiceGUI
        """
        if self.flags.get('notify',True):
            name = type(ui_event.sender).__name__
            value = self.values.get('click') if name.lower() == 'button' else getattr(ui_event,'value', name)
            ui.notify(f'{name}: {value}')
        logger.info(f'{self.name} <- {self.values}')
        return self.values

class MoverPanel(Panel):
    def __init__(self, 
        mover: Mover | None = None,
        name: str = 'Mover', 
        group: str | None = None, 
        panels: list[Panel] = list(),
        axes: Union[list, str] = 'XYZabc', 
        **kwargs
    ):
        super().__init__(name, group, panels, **kwargs)
        self.tool = mover
        
        self.axes = [*axes]
        self.buttons = {}
        self.current_attachment = ''
        self.attachment_methods = []
        self.method_map = {}
        
        self.flags['update_position'] = True
        return
    
    # Properties
    @property
    def mover(self) -> Mover:
        return self.tool
    
    def getLayout(self):
        axes = ['X','Y','Z','a','b','c']
        increments = ['-10','-1','-0.1',0,'+0.1','+1','+10']
        zpad = ['Z-10','Z-1','Z-0.1','Safe','Z+0.1','Z+1','Z+10']
        dpad_positions = {
            3:'Y+10',
            10:'Y+1',
            17:'Y+0.1',
            21:'X-10',22:'X-1',23:'X-0.1',24:'Home',25:'X+0.1',26:'X+1',27:'X+10',
            31:'Y-0.1',
            38:'Y-1',
            45:'Y-10'
        }
        with ui.card():
            ui.markdown(f'## {self.name}')
            with ui.row():
                with ui.grid(rows=7,columns=1).classes('gap-0'):
                    for z in zpad:
                        color = 'accent' if z.lower() == 'safe' else 'primary'
                        ui.button(z,color=color, on_click=self.listenEvents)
                with ui.grid(rows=7,columns=7).classes('gap-0'):
                    for d in range(7*7):
                        if d in dpad_positions:
                            color = 'accent' if dpad_positions[d].lower() == 'home' else 'primary'
                            ui.button(dpad_positions[d], color=color, on_click=self.listenEvents)
                        else:
                            ui.space()
        return
    
    def listenEvents(self, ui_event: UiEventArguments) -> dict[str, Any]:
        return super().listenEvents(ui_event)

# %%
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    left = MoverPanel()
    right = Panel('Right')
    gui = Panel('Outer', panels=[left,right])
    gui.runGUI()

# %%
if __name__ == '__main__':
    up = Panel('Up')
    down = Panel('Down')
    gui2 = Panel('Other', panels=[up,down])
    gui2.runGUI()
    
# %%
