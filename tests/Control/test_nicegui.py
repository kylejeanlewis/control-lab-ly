# %%
from __future__ import annotations
from abc import ABC, abstractmethod
import logging
import os
from threading import Thread
from typing import Union, Any, Protocol
import webbrowser

import keyboard
import nest_asyncio
from nicegui import ui, app
from nicegui.elements.button import Button
from nicegui.elements.dialog import Dialog
from nicegui.events import UiEventArguments
import numpy as np

nest_asyncio.apply()

logger = logging.getLogger(__name__)

class Panel:#(ABC):
    """
    Abstract Base Class (ABC) for Panel objects (i.e. GUI panels).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.

    ### Constructor
    Args:
        `name` (str, optional): name of panel. Defaults to ''.
        `group` (str | None, optional): name of group. Defaults to None.
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
    _default_values: dict[str, Any] = dict(click=None)
    _loaded_panels: list[Panel] = []
    _server_shutdown: list[bool] = [False]
    _shutdown_dialog: Dialog | None = None
    _thread: list[Thread] = []
    _used_names: list[str] = []
    def __init__(self, 
        tool: Any | None = None,
        name: str = '', 
        group: str | None = None,
        panels: list[Panel] = list(),
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            name (str, optional): name of panel. Defaults to ''.
            group (str | None, optional): name of group. Defaults to None.
            panels (list[Panel], optional): list of sub-panels. Defaults to list().
        """
        self._name = ''
        self.name = name
        self.group = group
        self.panels: list[Panel] = panels
        
        self.elements = dict()
        self.flags = self._default_flags.copy()
        self.tool = tool
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
    @ui.refreshable
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
    def listenEvents(self, ui_event: UiEventArguments) -> tuple[str, dict[str, Any]]:
        """
        Listen to events and act on values

        Args:
            ui_event (UiEventArguments): event object from NiceGUI

        Returns:
            tuple[str, dict[str, Any]]: dictionary of values
        """
        event = type(ui_event.sender).__name__
        if event.lower() == 'button':
            sender: Button = ui_event.sender
            value = sender.text
            self.values.update(dict(click=value))
        else:
            self.values.update(dict(click=None))
        self._show_values(ui_event=ui_event)
        return event, self.values.copy()

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
    
    def getMultiChannelLayout(self):
        if 'channels' not in dir(self.tool):
            return self.getLayout()
        channels: dict = self.tool.channels
        if len(channels) == 0:
            return self.getLayout()
        
        with ui.carousel(animated=True, arrows=True, navigation=True).props('height=180px'):
            for channel_id,tool in channels.items():
                with ui.carousel_slide().classes('p-0'):
                    self.getLayout() 
        # with ui.card():
        #     with ui.tabs().classes('w-full') as ui_tabs:
        #         tabs = []
        #         tools = []
        #         default_tab = None
        #         for channel_id,tool in channels.items():
        #             tab = ui.tab(str(channel_id))
        #             tabs.append(tab)
        #             tools.append(tool)
        #         default_tab = tabs[0] if default_tab is None else default_tab
            
        #     with ui.tab_panels(ui_tabs, value=default_tab).classes('w-full'):
        #         for tab,tool in zip(tabs, tools):
        #             with ui.tab_panel(tab):
        #                 self.getLayout()
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
                    # panel.getLayout()
                    panel.getMultiChannelLayout()
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
            self.getMultiChannelLayout()
            # self.getLayout()
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
        if self not in self._loaded_panels:
            self._loaded_panels.append(self)
        
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
                for panel in self._loaded_panels:
                    tab = ui.tab(panel.name)
                    tabs.append(tab)
                    if panel.name == self.name:
                        default_tab = tab
                default_tab = tabs[-1] if default_tab is None else default_tab
            
            with ui.tab_panels(ui_tabs, value=default_tab).classes('w-full'):
                for tab,panel in zip(tabs, self._loaded_panels):
                    with ui.tab_panel(tab):
                        if len(panel.panels):
                            with ui.row().classes('w-full justify-center'):
                                for panel in panel.panels:
                                    panel.getMultiChannelLayout()
                                    # panel.getLayout()
                        else:
                            panel.getMultiChannelLayout()
                            # panel.getLayout()
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
        if self._server_shutdown[0]:
            logging.error('Server has been shutdown. Kernel restart required.')
            return
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
            cls._server_shutdown = [True]
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

class MoverPanel(Panel):
    def __init__(self, 
        mover: Mover | None = None,
        name: str = 'Mover', 
        group: str | None = None, 
        panels: list[Panel] = list(),
        axes: Union[list, str] = 'xyzabc', 
        **kwargs
    ):
        super().__init__(name=name, group=group, panels=panels, **kwargs)
        self.tool = mover
        self.axes = [*axes.lower()]
        
        self.current_attachment = ''
        self.attachment_methods = []
        self.method_map = {}
        return
    
    # Properties
    @property
    def mover(self) -> Mover:
        return self.tool
    
    @ui.refreshable
    def getLayout(self):
        axes = [*'xyzabc']
        zpad = ['Z+10','Z+1','Z+0.1','Safe','Z-0.1','Z-1','Z-10']
        dpad_positions = {
            3:'Y+10',10:'Y+1',17:'Y+0.1',
            21:'X-10',22:'X-1',23:'X-0.1',24:'Home',
            25:'X+0.1',26:'X+1',27:'X+10',
            31:'Y-0.1',38:'Y-1',45:'Y-10'
        }
        tool_position = list(np.concatenate(self.mover.tool_position))
        positions = {axis:value for axis,value in zip(axes,tool_position)}
        sliders = {axis:value for axis,value in positions.items() if axis in [*'abc']}
        self.values.update(dict(position=positions, sliders=sliders))
        
        with ui.card():
            ui.markdown(f'## {self.name}')
            with ui.row().classes('w-full justify-center'):
                with ui.grid(rows=7,columns=1).classes('gap-0') as grid:
                    grid.set_visibility(('z' in self.axes))
                    for z in zpad:
                        color = 'accent' if z.lower() == 'safe' else 'primary'
                        ui.button(z,color=color, on_click=self.listenEvents)
                with ui.grid(rows=7,columns=7).classes('gap-0'):
                    for d in range(7*7):
                        if d in dpad_positions:
                            button_label = dpad_positions[d].lower()
                            color = 'accent' if button_label == 'home' else 'primary'
                            visible = (button_label == 'home') or (button_label[0] in self.axes)
                            ui.button(button_label, color=color, on_click=self.listenEvents).set_visibility(visible)
                        else:
                            ui.space()
            for axis,rotations in zip([*'abc'],('yaw','pitch','roll')):
                if axis not in self.axes:
                    continue
                with ui.row().classes('w-full justify-between'):
                    ui.label(rotations.title())
                    slider = ui.slider(min=-180,max=180,step=1,value=positions[axis])#, on_change=self.listenEvents)
                    slider.on('update:model-value', self.listenEvents, throttle=1.0, leading_events=False)
                    slider.bind_value(self.values['sliders'], axis.lower())
                    slider.props('label True').classes('w-3/4')
            with ui.row().classes('w-full justify-center'):
                for axis in self.axes:
                    number = ui.number(axis, precision=2, step=0.1).bind_value(self.values['position'], axis.lower())
                    number.classes('w-1/12')
            with ui.row().classes('w-full justify-center'):
                ui.button('Go', on_click=self.listenEvents)
                ui.button('Clear', on_click=self.listenEvents)
                ui.button('Reset', on_click=self.listenEvents)
        return
    
    def listenEvents(self, ui_event: UiEventArguments) -> tuple[str, dict[str, Any]]:
        event, values = super().listenEvents(ui_event=ui_event)
        axes = [*'xyzabc']
        tool_position = list(np.concatenate(self.mover.tool_position))
        
        _event = event.upper()
        if _event == 'BUTTON':
            click = self.values.get('click')
            _click = click.upper() if click is not None else ''
            if _click == 'CLEAR':
                positions = {axis:value for axis,value in zip(axes,tool_position)}
                logger.debug(f'Reset values to: {positions}')
                self.values.update(position=positions)
            elif _click == 'GO':
                pos_val = self.values.get('position')
                if pos_val is not None:
                    position = np.array([pos_val.get(axis,tool_position[i]) for i,axis in enumerate(axes)])
                    position = position.reshape((2,3))
                else:
                    position = self.mover.tool_position
                logger.debug(f'Go to: {position}')
                self.mover.safeMoveTo(*position)
            elif _click == 'HOME':
                logger.debug('Home')
                self.mover.home()
            elif _click == 'RESET':
                logger.debug('Reset')
                self.mover.reset()
            elif _click == 'SAFE':
                try:
                    coord = tool_position[:2] + [self.mover.heights['safe']]
                except (AttributeError,KeyError):
                    coord = self.mover._transform_out(coordinates=self.mover.home_coordinates, tool_offset=True)
                    coord = (*tool_position[:2], coord[2])
                if tool_position[2] >= coord[2]:
                    print('Already cleared safe height. Staying put...')
                else:
                    orientation = tool_position[-3:]
                    logger.debug('Safe')
                    self.mover.moveTo(coord, orientation)
            elif _click[0] in [*'XYZ']:
                    axis = _click[0].lower()
                    displacement = float(click[1:])
                    logger.debug(f"Axes: {axis}; Displacement: {displacement}")
                    self.mover.move(axis,displacement)
            else:
                ...
            self.getLayout.refresh()
        
        elif _event == 'SLIDER':
            pos_val = self.values.get('sliders')
            if pos_val is not None:
                position = np.array([pos_val.get(axis,tool_position[i]) for i,axis in enumerate(axes)])
                position = position.reshape((2,3))
            else:
                position = self.mover.tool_position
            
            if not (position[1] == self.mover.tool_position[1]).all():
                logger.debug(f'Rotate to: {position[1]}')
                self.mover.rotateTo(position[1])
            # time.sleep(1)
            self.getLayout.refresh()
        
        else:
            ...
        return event, values

# %%
