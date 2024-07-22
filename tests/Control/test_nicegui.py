# %%
from __future__ import annotations
import logging
import nest_asyncio
import os
from threading import Thread
from typing import Optional, Union, Any
import webbrowser

from nicegui import ui, app
from nicegui.events import ValueChangeEventArguments

logger = logging.getLogger(__name__)
panels: list[Panel] = []
logging.basicConfig(level=logging.DEBUG)
nest_asyncio.apply()

# %%
class Panel:#(ABC):
    """
    Abstract Base Class (ABC) for Panel objects (i.e. GUI panels).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.

    ### Constructor
    Args:
        `name` (str, optional): name of panel. Defaults to ''.
        `group` (Optional[str], optional): name of group. Defaults to None.
        `font_sizes` (tuple[int], optional): list of font sizes. Defaults to (14,12,10,8,6).
        `theme` (str, optional): name of theme. Defaults to 'LightGreen'.
        `typeface` (str, optional): name of typeface. Defaults to "Helvetica".
    
    ### Attributes
    #### Class
    - `font_sizes` (tuple[int]): list of font sizes
    - `theme` (str): name of theme
    - `typeface` (str): name of typeface
    #### Instance
    - `flags` (dict[str, bool]): keywords paired with boolean flags
    - `group` (str): name of group
    - `name` (str): name of panel
    - `tool` (Callable): tool to be controlled
    - `window` (sg.Window): Window object
    
    ### Methods
    #### Abstract
    - `getLayout`: build `sg.Column` object
    - `listenEvents`: listen to events and act on values
    #### Public
    - `arrangeElements`: arrange elements in a horizontal, vertical, or cross-shape pattern
    - `close`: exit the application
    - `configure`: configure GUI defaults
    - `getButtons`: get a list of panel buttons
    - `getInputs`: get the layout for the input section
    - `getWindow`: build `sg.Window` object
    - `pad`: add spacer in GUI
    - `parseInput`: parse inputs from GUI
    - `runGUI`: run the GUI loop
    - `setFlag`: set flags by using keyword arguments
    """
    
    _default_flags: dict[str, bool] = dict(notify=True)
    _default_values: dict[str, Any] = dict()
    _shutdown_dialog = None
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
        self._thread: Thread | None = None
        # self.configure()
        return
    
    def __del__(self):
        self.close(force=True)
    
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
        """
        Build the UI layout

        Args:
            title (str, optional): title of layout. Defaults to 'Panel'.
            title_font_level (int, optional): index of font size from levels in `font_sizes`. Defaults to 0.

        Returns:
            sg.Column: Column object
        """
        self.values = dict(
            checkbox1=True,
            notify=False,
            radio1='B',
            input1='type here',
            select1=None
        )
        with ui.card():
            ui.markdown(f'## {self.name}')
            ui.button('Button', on_click=lambda: ui.notify('Click'))
            with ui.row():
                ui.checkbox('Checkbox', on_change=self.showValues).bind_value(self.values, 'checkbox1')
                ui.switch('Switch', on_change=self.showValues).bind_value(self.values, 'notify')
            ui.radio(['A', 'B', 'C'], value='A', on_change=self.showValues).props('inline').bind_value(self.values, 'radio1')
            with ui.row():
                ui.input('Text input', on_change=self.showValues).bind_value(self.values, 'input1')
                ui.select(['One', 'Two'], value='One', on_change=self.showValues).bind_value(self.values, 'select1')
            ui.link('And many more...', '/documentation').classes('mt-8')
        return

    # @abstractmethod
    def listenEvents(self, ui_event: ValueChangeEventArguments) -> dict[str, str]:
        """
        Listen to events and act on values

        Args:
            event (str): event triggered
            values (dict[str, str]): dictionary of values from window

        Returns:
            dict: dictionary of updates
        """
        event = type(ui_event.sender).__name__
        values = self.values
        return self.showValues(ui_event=ui_event)

    @classmethod
    def close(cls, force: bool = False):
        """Exit the application"""
        if not force:
            proceed = input('Once GUI server closed, unable to start up again until kernel is restarted. Proceed? (y/n)')
            if proceed.strip().lower() != 'y':
                logger.warning('Abort closing GUI server.')
                return
        try:
            cls._shutdown_dialog.close()
            app.shutdown()
        except Exception as e:
            logger.exception(e)
        return

    @classmethod
    def configure(cls, **kwargs):
        """Configure GUI defaults"""
        with ui.dialog() as dialog, ui.card():
            def _close():
                cls._shutdown_dialog.close()
                cls.close(force=True)
                return
            cls._shutdown_dialog = dialog
            ui.label('Once GUI server closed, unable to start up again until kernel is restarted. Proceed?')
            with ui.row().classes('w-full justify-center'):
                ui.button('No', on_click=cls._shutdown_dialog.close)
                ui.button('Yes', on_click=_close, color='negative')
        return

    def getMultiPanel(self):
        """
        Build multi-panel page
        """
        @ui.page(self.page_address)
        async def get_multi_panel_page():
            """Build multi panel page"""
            self.configure()
            with ui.row().classes('w-full justify-between items-center'):
                ui.markdown(f'# {self.name}')
                ui.button('Shutdown', on_click=self._shutdown_dialog.open, color='negative')
                
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
            ui.button('Shutdown', on_click=self._shutdown_dialog.open, color='negative')
            
            await ui.context.client.connected()
            logging.debug(f'Connected: {self.root_address}{self.page_address}')
            await ui.context.client.disconnected()
            logging.debug(f'Disconnected: {self.root_address}{self.page_address}')
            return
        return self.page_address
    
    def getWindow(self):
        """
        Get landing page window
        """
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
                ui.button('Shutdown', on_click=self._shutdown_dialog.open, color='negative')
                
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
            title (str, optional): title of window. Defaults to 'Application'.
        """
        # self.configure()
        self.getWindow()
        if 'NICEGUI_HOST' in os.environ:
            webbrowser.open(f'http://{self.root_address}{self.page_address}')
        elif self._thread is None:
            self._port = int(os.environ.get('NICEGUI_PORT', '8080'))
            kwargs.update(dict(title=title, reload=False, host=self.host, port=self.port, show=False))
            self._thread = Thread(target=ui.run, kwargs=kwargs)
            self._thread.start()
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

    def showValues(self, ui_event: ValueChangeEventArguments):
        logger.info(f'{self.name} <- {self.values}')
        if self.flags.get('notify',True):
            name = type(ui_event.sender).__name__
            ui.notify(f'{name}: {ui_event.value}')
        return

# %%
if __name__ == '__main__':
    left = Panel('Left')
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
