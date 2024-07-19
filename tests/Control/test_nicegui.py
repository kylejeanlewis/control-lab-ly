# %%
from __future__ import annotations
import logging
import nest_asyncio
from typing import Optional, Union, Any

from nicegui import ui, app
from nicegui.events import ValueChangeEventArguments

logger = logging.getLogger(__name__)
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
    
    _default_flags: dict[str, bool] = dict()
    _default_values: dict[str, Any] = dict(
        checkbox1=True,
        notify=False,
        radio1='B',
        input1='type here',
        select1=None
    )
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
        self.name = name
        self.group = group
        self.panels: list[Panel] = panels
        
        self.flags = self._default_flags.copy()
        self.tool = None
        self.configure()
        
        self.values = self._default_values.copy()
        return
    
    def __del__(self):
        self.close()
    
    @property
    def page_address(self) -> str:
        return f'/{self.name}'
    
    # @abstractmethod
    def getLayout(self):
        """
        Build `sg.Column` object

        Args:
            title (str, optional): title of layout. Defaults to 'Panel'.
            title_font_level (int, optional): index of font size from levels in `font_sizes`. Defaults to 0.

        Returns:
            sg.Column: Column object
        """
        with ui.card():
            ui.markdown(f'# {self.name}')
            # ui.button('Button', on_click=lambda: ui.notify('Click'))
            # with ui.row():
            #     ui.checkbox('Checkbox', on_change=self.showValues).bind_value(self.values, 'checkbox1')
            #     ui.switch('Switch', on_change=self.showValues).bind_value(self.values, 'notify')
            # ui.radio(['A', 'B', 'C'], value='A', on_change=self.showValues).props('inline').bind_value(self.values, 'radio1')
            # with ui.row():
            #     ui.input('Text input', on_change=self.showValues).bind_value(self.values, 'input1')
            #     ui.select(['One', 'Two'], value='One', on_change=self.showValues).bind_value(self.values, 'select1')
            # ui.link('And many more...', '/documentation').classes('mt-8')
        return

    # @abstractmethod
    def listenEvents(self, event:str, values:dict[str, str]) -> dict[str, str]:
        """
        Listen to events and act on values

        Args:
            event (str): event triggered
            values (dict[str, str]): dictionary of values from window

        Returns:
            dict: dictionary of updates
        """
        return

    @staticmethod
    def close():
        """Exit the application"""
        try:
            app.shutdown()
        except:
            pass
        return

    @classmethod
    def configure(cls, **kwargs):
        """Configure GUI defaults"""
        return

    def getMultiPanel(self, paginated: bool = False):
        if paginated:
            with ui.button_group():
                for panel in self.panels:
                    panel.getPage()
                    ui.button(panel.name, on_click=panel.redirect)
        else:
            with ui.row():
                for panel in self.panels:
                    panel.getLayout()
        ui.button('Shutdown', on_click=app.shutdown)
        return

    def getPage(self) -> str:
        """Build GUI page"""
        @ui.page(self.page_address)
        async def get_page():
            """Build GUI page"""
            self.getLayout()
            ui.button('Shutdown', on_click=app.shutdown)
            await ui.context.client.connected()
            print('Connected')
            await ui.context.client.disconnected()
            print('Disconnected')
            return
        return self.page_address
    
    def getWindow(self, paginated: bool = False):
        @ui.page('/')
        async def index():
            """Build landing page"""
            if len(self.panels):
                self.getMultiPanel(paginated=paginated)
            else:
                self.getPage()
                ui.navigate.to(f'/{self.name}')
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
        return ui.navigate.to(self.page_address)
    
    async def runGUI(self, title:str = 'Control-lab-ly', paginated: bool = False, **kwargs):
        """
        Run the GUI loop

        Args:
            title (str, optional): title of window. Defaults to 'Application'.
        """
        self.configure()
        self.getWindow(paginated=paginated)
        ui.run(title=title, reload=kwargs.get('reload', False))
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
        # for key, value in kwargs.items():
        #     self.flags[key] = value
        return

    def showValues(self, event: ValueChangeEventArguments):
        print(self.values)
        if self.values['notify']:
            name = type(event.sender).__name__
            ui.notify(f'{name}: {event.value}')
        return

# %%
if __name__ == '__main__':
    left = Panel('Left')
    right = Panel('Right')
    gui = Panel('Outer', panels=[left,right])
    gui.runGUI(reload=False, paginated=True)

# %%
