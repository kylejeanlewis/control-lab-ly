# %%
import sys
sys.path.append('../')
from tools.guibuilder import Builder, Popups
import PySimpleGUI as sg
from PySimpleGUI import WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT

WIDTH, HEIGHT = sg.Window.get_screen_size()
# THEME = 'LightGreen'
# BG_COLOR = '#d3dfda'
# FONT = "Helvetica"
# TITLE_SIZE = 12
# TEXT_SIZE = 10

# sg.theme(THEME)
# sg.set_options(
#     font=FONT,
#     background_color=BG_COLOR,
#     element_padding = (0,0)
#     )
# pop = Popups()

class GUI(object):
    def __init__(self):
        super().__init__()
        return

    def build_window(self):
        bd = Builder()
        size_B = (7,2)
        size_I = (28,1)
        size = (None,None)
        left_width = WIDTH * 0.4
        right_width = WIDTH * 0.18
        short_height = HEIGHT * 0.15
        mid_height = HEIGHT * 0.18
        long_height = HEIGHT * 0.4

        # CNC panel
        display_x = [
            [bd.getP(), bd.getB("X+10", size_B), bd.getB("X+1", size_B), bd.getB("X+0.1", size_B),
            sg.Button("<X>", size=size_B, font=(bd.font, bd.text_size), button_color=('#000000', '#ffffff')),
            bd.getB("X-0.1", size_B), bd.getB("X-1", size_B), bd.getB("X-10", size_B), bd.getP()],
            [bd.getS((-470,0), 0, 'h', (7*size_B[0], 10), '-X-SLIDE-')]
        ]
        display_x = sg.Frame('X-Position', display_x, background_color=bd.bg_color, element_justification='center', vertical_alignment='top')
        display_x = sg.Column([[bd.getP(), display_x, bd.getP()]], background_color=bd.bg_color, justification='center', element_justification='center', vertical_alignment='top', size=(left_width, short_height))
        control_x = [
            [bd.getText("Current position:", size, 'center')],
            [bd.getP(), sg.Input(0, justification='center', key='-X-POSITION-', font=(bd.font, bd.text_size), size=size_I), bd.getP()],
            [bd.getText('')],
            [bd.getP(), bd.getB("Go To", size_B), bd.getB("Clear", size_B), bd.getP()],
        ]
        control_x = sg.Column(control_x, background_color=bd.bg_color, justification='center', element_justification='left', vertical_alignment='top', size=(right_width, short_height))

        # Syringe panel
        syr = [bd.getP()]
        for i in range(5):
            name = f"Syringe {i}"
            display_syr = [
                [bd.getText(f"Reagent {i}", size, 'center', key=f'-REAGENT-{i}-')],
                [bd.getText("0 uL", size, 'center', key=f'-VOLUME-{i}-')],
                [bd.getS((0, 3000), 0, 'v', (10,10), f'-SYR-SLIDE-{i}-')],
                [bd.getB('V', key=f'-SYR-{i}-')]
            ]
            display_syr = sg.Frame(name, display_syr, background_color=bd.bg_color, element_justification='center', vertical_alignment='top')
            syr.append(display_syr)
        syr.append(bd.getP())
        display_syr = sg.Column([syr], background_color=bd.bg_color, justification='center', element_justification='center', vertical_alignment='top', size=(left_width, long_height))
        control_syr = [
            [bd.getText("Volume:", size, 'center')],
            [sg.Input(0, justification='center', key='-SYR-VOLUME-', font=(bd.font, bd.text_size), size=size_I)],
            [bd.getText('')],
            [bd.getP(), bd.getB("Aspirate", size_B), bd.getB("Dispense", size_B), bd.getP()],
            [bd.getP(), bd.getB("Fill", size_B), bd.getB("Empty", size_B), bd.getP()],
            [bd.getP(), bd.getC('all', size, '-ALL-SYR-'), bd.getP()]
        ]
        control_syr = sg.Column(control_syr, background_color=bd.bg_color, justification='center', element_justification='left', vertical_alignment='top', size=(right_width, long_height))

        # Spinner panel
        spi = [bd.getP()]
        for c in 'ABCD':
            name = f"Spinner {c}"
            display_spi = [
                [bd.getB('O', key=f'-SPI-{c}-')],
                [sg.Input(0, justification='center', key=f'-SPPED-{c}-', font=(bd.font, bd.text_size), size=(10,1)), bd.getText('rpm  ')],
                [sg.Input(0, justification='center', key=f'-DURATION-{c}-', font=(bd.font, bd.text_size), size=(10,1)), bd.getText('sec  ')],
                [bd.getB('Start', key=f'-SPI-START-{c}-')]
            ]
            display_spi = sg.Frame(name, display_spi, background_color=bd.bg_color, element_justification='center', vertical_alignment='top')
            spi.append(display_spi)
        spi.append(bd.getP())
        display_spi = sg.Column([spi], background_color=bd.bg_color, justification='center', element_justification='center', vertical_alignment='top', size=(left_width, mid_height))
        spi = [display_spi]
        control_spi = [
            [bd.getC('Use Recipe', size, '-RECIPE-USE-', True)],
            [bd.getText("Load Recipe:", size, 'center')],
            [bd.getI("", (15,1), f"-RECIPE-FILE-", enable_events=True), 
            sg.FileBrowse(size=(8,1), font=(bd.font, bd.text_size), key=f"-RECIPE-BROWSE-", initial_folder=None)],
            [bd.getText('')],
            [bd.getP(), bd.getB("Run Experiment", (16,1), "-RUN-RESET-"), bd.getP()]
        ]
        control_spi = sg.Column(control_spi, background_color=bd.bg_color, justification='center', element_justification='left', vertical_alignment='top', size=(right_width, mid_height))
        spi.append(control_spi)

        layout = [[display_x, control_x], [bd.getText('')], [display_syr, control_syr], [bd.getText('')], spi]
        self.window = sg.Window("Para-Spin", layout, enable_close_attempted_event=True, resizable=True, finalize=True)
        return

    def gui_loop(self, paths={}):
        """
        Run a loop to keep GUI window open
        - paths: dict of paths to save output
        """
        while True:
            event, values = self.window.read(timeout=20)
            ## 0. Exit loop
            if event in ('Ok', WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT, None):
                break
        return

    def run_program(self, paths={}, maximize=False):
        """
        Run program based on build_window and defined gui_loop
        - paths: dict of paths to save output
        - maximize: whether to maximize window
        """
        # try:
        #     savefolder = paths['savefolder']
        # except:
        #     savefolder = ''
        # self.savefolder = savefolder
        # if len(self.savefolder) == 0:
        #     self.savefolder = os.getcwd().replace('\\', '/')
        # elif not os.path.exists(self.savefolder):
        #     os.makedirs(self.savefolder)
        
        self.build_window()
        self.window.Finalize()
        if maximize:
            self.window.Maximize()
        self.window.bring_to_front()
        self.gui_loop(paths)
        self.window.close()
        return

if __name__ == '__main__':
    print(WIDTH, HEIGHT)
    gui = GUI()
    gui.run_program()
# %%
