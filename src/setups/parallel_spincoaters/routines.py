# %%
import time
import pandas as pd
import threading
import PySimpleGUI as sg
from PySimpleGUI import WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT

import spinutils
from gantt import gantt_plotter
import sys
sys.path.append('../')
from tools.guibuilder import Builder, Popups
print(f"Import: OK <{__name__}>")

PRINT_LOGS = True
MANUAL_FILL = True
SPIN_ONLY = True
FILL_ORDER = [4,3,1,0,2]

# Machine variables
CNC_SPEED = 250         # mm per second
T_PRIME = 2        # priming time for pump (second)
PREWET_CYCLES = 1       # number of times to aspirate/dispense for pre-wetting syringe
CALIB_ASPIRATE = 27
CALIB_DISPENSE = 23.5
VALVE_CHANNEL_OFFSET = 3
TRACK_BOUNDS = (-470, 0) # range of x along track

WIDTH, HEIGHT = sg.Window.get_screen_size()

macros = spinutils.Macros()
actuate = spinutils.Actuate(mute_debug=True)
pop = Popups()
macros.list_serial()
log_output = []


def log_now(string, force_print=False, save=True):
    '''
    Add log with timestamp
    - string: log message
    - force_print: whether to force display message in console

    Returns: log message with timestamp
    '''
    out = time.strftime("%H:%M:%S", time.localtime()) + ' >> ' + string
    if save:
        log_output.append(out)
    if PRINT_LOGS or force_print:
        print(out)
    return out


def write_log(out, connects):
    '''
    Write logs into txt files
    - out: list of log messages
    - connects: dataframe of connection information

    Returns: dictionary of log messages with tool names as keys
    '''
    with open('logs/activity_log.txt', 'w') as f:
        for line in out:
            f.write(line + '\n')
    with open('logs/tool_log.txt', 'w') as f:
        tools = connects.description.to_list()
        tool_log = {tool: [] for tool in tools}
        for line in out:
            if 'CNC align' in line:
                tool_log['cnc'].append(line)
            elif 'Syringe' in line:
                tool_log['pump'].append(line)
            elif 'Spinner' in line:
                order = line.split()[3].replace(':', '')
                tool_log[f'spin_{order}'].append(line)
        for k, v in tool_log.items():
            f.write(k + '\n')
            for line in v:
                f.write(line + '\n')
            f.write('\n')
    return tool_log


class Spinner(object):
    """
    'Spinner' class contains methods to control the spin coater unit.
    """
    def __init__(self, order, position, spin):
        self.order = order
        self.position = position
        self.spin = spin

        self.speed = 0
        self.busy = False
        self.complete = False
        self.etc = time.time()
        return

    def execute(self, t_soak, s_spin, t_spin):
        '''
        Executes the soak and spin steps
        - t_soak: soak time
        - s_spin: spin speed
        - t_spin: spin time

        Returns: None
        '''
        self.busy = True
        self.soak(t_soak)
        self.spin_off(s_spin, t_spin)
        self.busy = False
        return

    def soak(self, seconds):
        '''
        Executes the soak step
        - seconds: soak time

        Returns: None
        '''
        self.speed = 0
        if seconds:
            log_now(f'Spinner {self.order}: start soak')
            time.sleep(seconds)
            # actuate.run_spin_step(self.spin, speed, seconds)
            log_now(f'Spinner {self.order}: end soak')
        return

    def spin_off(self, speed, seconds):
        '''
        Executes the spin step
        - speed: spin speed
        - seconds: spin time

        Returns: None
        '''
        self.speed = speed
        log_now(f'Spinner {self.order}: start spin ({speed}rpm)')
        actuate.run_spin_step(self.spin, speed, seconds)
        log_now(f'Spinner {self.order}: end spin')
        self.speed = 0
        return


class Syringe(object):
    """
    'Syringe' class contain methods to control the pump and the valve unit.
    """
    def __init__(self, order, offset, capacity, pump):
        self.order = order
        self.offset = offset
        self.capacity = capacity
        self.pump = pump

        self.reagent = ''
        self.volume = 0
        self.t_prime = T_PRIME
        self.prev_action = ''
        self.busy = False
        return

    def aspirate(self, vol, speed=3000, spin_only_mode=False, log=True):
        '''
        Adjust the valve and aspirate reagent
        - vol: volume
        - speed: speed of pump rotation

        Returns: None
        '''
        self.busy = True
        vol = min(vol, self.capacity - self.volume)
        log_now(f'Syringe {self.order}: aspirate {vol}uL {self.reagent}...', save=log)

        if vol == 0:
            pass
        else:
            t_aspirate = vol / speed * CALIB_ASPIRATE
            if self.prev_action == '':
                t_aspirate *= 1.3
            if self.prev_action == 'aspirate':
                t_aspirate *= 1
            if self.prev_action == 'dispense':
                t_aspirate *= 1.6
            print(t_aspirate)
            t_prime = 50 / speed * CALIB_ASPIRATE
            pump_speed = -abs(speed)
            if not spin_only_mode:
                actuate.dispense(self.pump, pump_speed, t_prime, t_aspirate, self.order+VALVE_CHANNEL_OFFSET)
            self.volume += vol
        log_now(f'Syringe {self.order}: done', save=log)
        self.prev_action = 'aspirate'
        self.busy = False
        return

    def cycle(self, vol, speed=3000):
        self.aspirate(vol, speed=speed, log=False)
        self.dispense(vol, speed=speed, force_dispense=True, log=False)
        return

    def dispense(self, vol, speed=3000, force_dispense=False, log=True):
        '''
        Adjust the valve and dispense reagent
        - vol: volume
        - speed: speed of pump rotation
        - force_dispense: continue with dispense even if insufficient volume in syringe

        Returns: None
        '''
        self.busy = True
        if vol > self.volume and not force_dispense:
            log_now(f'Syringe {self.order}: Current volume too low for required dispense', save=log)
            log_now(f'Syringe {self.order}: done', save=log)
            return
        if not force_dispense:
            vol = min(vol, self.volume)
        log_now(f'Syringe {self.order}: dispense {vol}uL {self.reagent}...', save=log)

        if vol == 0 and not force_dispense:
            pass
        else:
            t_dispense = vol / speed * CALIB_DISPENSE
            if self.prev_action == 'aspirate':
                t_dispense *= 1.55
            if self.prev_action == 'dispense':
                t_dispense *= 1
            print(t_dispense)
            t_prime = 50 / speed * CALIB_DISPENSE
            pump_speed = abs(speed)
            actuate.dispense(self.pump, pump_speed, t_prime, t_dispense, self.order+VALVE_CHANNEL_OFFSET)
            self.volume -= vol
        log_now(f'Syringe {self.order}: done', save=log)
        self.prev_action = 'dispense'
        self.busy = False
        return

    def empty(self):
        '''
        Adjust the valve and empty syringe

        Returns: None
        '''
        self.dispense(self.capacity, speed=3000, force_dispense=True)
        self.volume = 0
        return

    def fill(self, reagent, vol=None, prewet=True, spin_only_mode=False):
        '''
        Adjust the valve and fill syringe with reagent
        - reagent: reagent to be filled in syringe
        - vol: volume

        Returns: None
        '''        
        self.reagent = reagent
        if vol == None:
            vol = self.capacity - self.volume

        if prewet and not spin_only_mode:
            log_now(f'Syringe {self.order}: pre-wet syringe...')
            for c in range(PREWET_CYCLES):
                if c == 0:
                    self.cycle(vol*1.1, 3000)
                else:
                    self.cycle(200, 3000)
                time.sleep(1)
            log_now(f'Syringe {self.order}: done')

        self.aspirate(vol, speed=3000, spin_only_mode=spin_only_mode)
        return

    def prime(self):
        self.busy = True
        actuate.dispense(self.pump, -300, self.t_prime, 0, self.order+VALVE_CHANNEL_OFFSET)
        self.busy = False
        return
    
    def rinse(self, rinse_cycles=3):
        log_now(f'Syringe {self.order}: rinsing syringe...')
        for _ in range(rinse_cycles):
            self.cycle(2000)
        log_now(f'Syringe {self.order}: done')
        return


class Setup(object):
    """
    'Setup' class contains methods to control the cnc arm, as well as coordinate the other units.
    """
    def __init__(self, conn_df, syringe_offsets, syringe_capacities, fill_position, dump_position, spin_positions, diagnostic=True):
        # Read state file
        with open('logs/save_state.txt', 'r') as f:
            state_log = f.readlines()
        for l, log in enumerate(state_log):
            state_log[l] = float(log.split()[-1])

        # Establish connections and initialise
        self.cnc = None
        self.pump = None
        self.spins = []
        self.current_x = state_log[-1]
        self.connect(conn_df)

        self.at_home = False
        self.current_x = 0
        self.n_spins = len(self.spins)
        self.home()

        # Set parameters
        self.syringe_offsets = syringe_offsets
        self.syringe_capacities = syringe_capacities
        self.fill_position = fill_position
        self.dump_position = dump_position
        self.spin_positions = spin_positions

        # Prepare syringes and reagents
        self.reagents = []
        self.syringes = []
        self.n_syringes = len(syringe_offsets)
        for n in range(self.n_syringes):
            offset = syringe_offsets[n]
            capacity = syringe_capacities[n]
            syringe = Syringe(n, offset, capacity, self.pump)
            syringe.volume = state_log[n]
            self.syringes.append(syringe)
            self.reagents.append('')

        # Prepare spinners and chucks
        self.spinners = []
        self.n_spinners = len(spin_positions)
        if self.n_spins != self.n_spinners:
            print('Ensure number of spin addresses and spin positions are equal!')
        for n in range(self.n_spinners):
            position = spin_positions[n]
            spin = self.spins[n]
            self.spinners.append(Spinner(n, position, spin))
        
        if diagnostic:
            self.run_diagnostic()
        self.aligning = 0
        self.pumping = False
        return

    def align(self, syringe_offset, position):
        '''
        Position the relevant syringe with the relevant spinner / station
        - syringe_offset: the offset between syringe and cnc arm
        - position: location of the relevant spinner / station

        Returns: new x position of cnc arm
        '''
        position = min(max(position, TRACK_BOUNDS[0]), TRACK_BOUNDS[1])
        distance = position - self.current_x - syringe_offset
        self.current_x = actuate.move_dispense_rel(self.cnc, self.current_x, distance)
        self.at_home = False
        t_align = abs(distance) / CNC_SPEED + 2
        time.sleep(t_align)
        log_now(f'CNC align: in position')
        self.aligning = 0
        return self.current_x

    def coat(self, spinner, syringe, vol, t_soak, s_spin, t_spin, new_thread=True, rest_home=True):
        '''
        Aligns the syringe and perform a spincoating step
        - spinner: relevant spinner object
        - syringe: relevent syringe object
        - vol: volume
        - t_soak: soak time
        - s_spin: spin speed
        - t_spin: spin time
        - new_thread: whether to run the spinner in a separate work thread
        - rest_home: whether to send cnc arm to home during rest

        Returns: new work thread or None
        '''
        if vol:
            log_now(f'CNC align: syringe {syringe.order} with spinner {spinner.order}...')
            self.align(syringe.offset, spinner.position)
            while spinner.busy:
                time.sleep(0.5)
            spinner.busy = True
            syringe.dispense(vol, speed=3000)

        # Start new thread from here
        spinner.etc = time.time() + t_soak + t_spin + 1
        if new_thread:
            t = threading.Thread(target=spinner.execute, name=f'spin_{spinner.order}', args=(t_soak, s_spin, t_spin))
            t.start()
            if rest_home:
                log_now(f'CNC align: move to rest position...')
                self.align(0, self.dump_position)
                self.prime_syringes()
            return t
        else:
            if rest_home:
                log_now(f'CNC align: move to rest position...')
                self.align(0, self.dump_position)
            spinner.execute(t_soak, s_spin, t_spin)
            self.prime_syringes()
        return None

    def connect(self, df):
        '''
        Establish connections with the hardware
        - df: config dataframe

        Returns: None
        '''
        cnc_arg = df[df.description=='cnc'].iloc[0, -2:].values
        pump_arg = df[df.description=='pump'].iloc[0, -2:].values
        spin_args = df[df.description.str.contains('spin_')].iloc[:, -2:].values

        self.cnc = macros.open_serial(*cnc_arg)

        # Connect with pump and initialise by closing all valves
        self.pump = macros.open_serial(*pump_arg)
        actuate.run_solenoid(self.pump, 9)

        for spin_arg in spin_args:
            spin = macros.open_serial(*spin_arg)
            self.spins.append(spin)
        return

    def empty_syringes(self, syringe_nums, manual=False):
        '''
        Empty relevant syringes
        - syringe_nums: list of syringes to be emptied
        - manual: supervised emptying of syringes

        Returns: None
        '''
        # input("Ready to empty? Press 'Enter' to continue.")
        # pop.notif("Ready to empty?")
        self.pumping = True
        for syringe_num in syringe_nums:
            syringe = self.syringes[syringe_num]
            if not manual:
                log_now(f'CNC align: syringe {syringe.order} with dump station...')
                self.align(syringe.offset, self.dump_position)
            else:
                log_now(f'CNC align: syringe {syringe.order} with dump station...')
                self.align(0, self.dump_position)
                # input(f"Syringe {syringe.order} ready? Press 'Enter' to continue.")
                # pop.notif(f"Syringe {syringe.order} ready?")
            syringe.empty()

            syringe.reagent = ''
            self.reagents[syringe_num] = ''
        self.pumping = False
        return
    
    def fill_syringes(self, syringe_nums, reagents, vol=[], manual=False, prewet=True, spin_only_mode=False):
        '''
        Fill relevant syringes
        - syringe_nums: list of syringes to be filled
        - reagents: list of reagents to be filled
        - vol: list of volumes of each reagent to fill
        - manual: supervised filling of syringes

        Returns: None
        '''
        self.pumping = True
        if len(vol) == 0:
            vol = [0 for _ in range(len(syringe_nums))]
        # input("Ready to fill? Press 'Enter' to continue.")
        # pop.notif("Ready to fill?")

        fill_order = FILL_ORDER
        if len(fill_order) != len(syringe_nums):
            fill_order = [s for s in range(len(syringe_nums))]
        
        syringe = None
        for s in fill_order:
            syringe_num = syringe_nums[s]
            if vol[s] == 0:
                syringe = self.syringes[syringe_num]
                syringe.fill(reagents[s], vol[s], prewet=False)
                self.reagents[syringe_num] = reagents[s]
                continue
            if syringe:
                syringe.prime()
            syringe = self.syringes[syringe_num]
            if not manual:
                log_now(f'CNC align: syringe {syringe.order} with fill station...')
                self.align(syringe.offset, self.fill_position)
            else:
                log_now(f'CNC align: syringe {syringe.order} with fill station...')
                self.align(0, self.fill_position)
                if not spin_only_mode:
                    # input(f"Syringe {syringe.order} ready? Press 'Enter' to continue.")
                    # pop.notif(f"Syringe {syringe.order} ready?")
                    pass
            syringe.fill(reagents[s], vol[s], prewet=prewet, spin_only_mode=spin_only_mode)
            self.reagents[syringe_num] = reagents[s]
        # input("Ready to proceed? Press 'Enter' to continue.")
        # pop.notif("Ready to proceed?")
        syringe.prime()
        self.pumping = False
        return

    def home(self):
        '''
        Moves cnc arm to home position

        Returns: None
        '''
        if self.at_home:
            return self.current_x
        log_now('CNC align: go home...')
        current_x = actuate.home_dispense(self.cnc)
        distance = self.current_x - current_x
        t_home = abs(distance) / (CNC_SPEED/10) + 1
        time.sleep(t_home)
        log_now(f'CNC align: in position')

        self.at_home = True
        self.current_x = current_x
        return self.current_x

    def prime_syringes(self):
        for syringe in self.syringes:
            syringe.prime()
        return

    def rinse_syringes(self):
        self.pumping = True
        for syringe in self.syringes:
            syringe.empty()
            syringe.rinse()
        self.pumping = False
        return

    def run_diagnostic(self):
        try:
            for i, spinner in enumerate(self.spinners):
                t = threading.Thread(target=spinner.spin_off, name=f'spin_diag_{i}', args=(2000, 2))
                t.start()

            log_now(f'CNC align: move to max distance...')
            self.align(0, TRACK_BOUNDS[0])
            log_now(f'CNC align: move to rest position...')
            self.align(0, self.dump_position)

            for syringe in self.syringes:
                t_prime = 1.4
                actuate.dispense(self.pump, -2000, t_prime, 0, syringe.order+VALVE_CHANNEL_OFFSET)

            connects = [self.cnc, self.pump] + self.spins
            if any([True for connect in connects if connect==None]):
                print("Check hardware / connection!")
            else:
                print("Hardware / connection ok!")
        except:
            print("Check hardware / connection!")
        return


class Controller(object):
    """
    'Controller' class contains high-level methods to take in instructions and conduct the steps.
    """
    def __init__(self, config_file, position_check=False, diagnostic=True):
        dfs = pd.read_excel(config_file, None)
        self.connects_df = dfs['connects']
        self.syringes_df = dfs['syringes']
        self.positions_df = dfs['positions']
        self.steps_df = pd.DataFrame()

        offsets = self.syringes_df.offset.to_list()
        capacities = self.syringes_df.capacity.to_list()
        fill, dump, *spin = self.positions_df.position.to_list()
        self.setup = Setup(self.connects_df, offsets, capacities, fill, dump, spin, diagnostic=diagnostic)
        if position_check:
            self.check_positions()

        self.assignment = []
        self.spin_threads = []
        self.threads = {}
        self.spin_only_mode = False

        self.stop = False
        self.unfreeze = False
        self.selected_syringe = None
        self.selected_spinner = None
        return

    def build_window(self):
        """
        Build GUI window from blocks provided in guibuilder.Builder object
        """
        bd = Builder()
        size_B = (7,2)
        size_I = (28,1)
        size = (None,None)
        left_width = WIDTH * 0.4
        right_width = WIDTH * 0.18
        short_height = HEIGHT * 0.15
        mid_height = HEIGHT * 0.18
        long_height = HEIGHT * 0.4

        # CNC panel left
        display_x = [
            [bd.getP(), bd.getB("X-10", size_B), bd.getB("X-1", size_B), bd.getB("X-0.1", size_B),
            sg.Button("<X>", size=size_B, font=(bd.font, bd.text_size), button_color=('#000000', '#ffffff')),
            bd.getB("X+0.1", size_B), bd.getB("X+1", size_B), bd.getB("X+10", size_B), bd.getP()],
            [bd.getS(TRACK_BOUNDS, 0, 'h', (7*size_B[0], 10), '-X-SLIDE-')]
        ]
        display_x = sg.Frame('X-Position', display_x, background_color=bd.bg_color, element_justification='center', vertical_alignment='top', key = '-X-MODULE-')
        display_x = sg.Column([[bd.getP(), display_x, bd.getP()]], background_color=bd.bg_color, justification='center', element_justification='center', vertical_alignment='top', size=(left_width, short_height))
        
        # CNC panel right
        control_x = [
            [bd.getText("Current position:", size, 'center')],
            [bd.getP(), sg.Input(0, justification='center', key='-X-POSITION-', font=(bd.font, bd.text_size), size=size_I, enable_events=True), bd.getP()],
            [bd.getText('')],
            [bd.getP(), bd.getB("Go To", size_B), bd.getB("Clear", size_B), bd.getP()],
        ]
        control_x = sg.Column(control_x, background_color=bd.bg_color, justification='center', element_justification='left', vertical_alignment='top', size=(right_width, short_height))

        # Syringe panel left
        syr = [bd.getP()]
        for i in range(self.setup.n_syringes):
            syringe = self.setup.syringes[i]
            name = f"Syringe {i}"
            display_syr = [
                [bd.getText(f"Reagent {i}", size, 'center', True, key=f'-REAGENT-{i}-')],
                [bd.getText(f"{syringe.volume} uL", size, 'center', key=f'-VOLUME-{i}-')],
                [sg.Slider((0, syringe.capacity), syringe.volume, orientation='v', s=(10,10), k=f'-SYR-SLIDE-{i}-', disable_number_display=True, font=(bd.font, bd.text_size), background_color=bd.bg_color)],
                [bd.getB('▼', key=f'-SYR-SELECT-{i}-')]
            ]
            display_syr = sg.Frame(name, display_syr, background_color=bd.bg_color, element_justification='center', vertical_alignment='top', key=f'-SYRINGE-{i}-MODULE-')
            syr.append(display_syr)
        syr.append(bd.getP())
        display_syr = sg.Column([syr], background_color=bd.bg_color, justification='center', element_justification='center', vertical_alignment='top', size=(left_width, long_height))
        
        # Syringe panel right
        control_syr = [
            [bd.getText("Volume:", size, 'center')],
            [sg.Input(0, justification='center', key='-SYR-VOLUME-', font=(bd.font, bd.text_size), size=size_I)],
            [bd.getText('')],
            [bd.getP(), bd.getB("Aspirate", size_B), bd.getB("Dispense", size_B), bd.getP()],
            [bd.getP(), bd.getB("Fill", size_B), bd.getB("Empty", size_B), bd.getP()],
            [bd.getP(), bd.getC('all', size, '-ALL-SYR-'), bd.getP()]
        ]
        control_syr = sg.Column(control_syr, background_color=bd.bg_color, justification='center', element_justification='left', vertical_alignment='top', size=(right_width, long_height))

        # Spinner panel left
        spi = [bd.getP()]
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        for i in range(self.setup.n_spinners):
            c = alphabet[i]
            name = f"Spinner {c}"
            display_spi = [
                [bd.getB('●', key=f'-SPI-SELECT-{i}-')],
                [sg.Input(0, justification='center', key=f'-SPEED-{i}-', font=(bd.font, bd.text_size), size=(5,1), enable_events=True), bd.getText('rpm  ')],
                [sg.Input(0, justification='center', key=f'-DURATION-{i}-', font=(bd.font, bd.text_size), size=(5,1), enable_events=True), bd.getText('sec  ')],
                [bd.getB('Start', key=f'-SPI-START-{i}-')]
            ]
            display_spi = sg.Frame(name, display_spi, background_color=bd.bg_color, element_justification='center', vertical_alignment='top', key=f'-SPINNER-{i}-MODULE-')
            spi.append(display_spi)
        spi.append(bd.getP())
        display_spi = sg.Column([spi], background_color=bd.bg_color, justification='center', element_justification='center', vertical_alignment='top', size=(left_width, mid_height))
        spi = [display_spi]

        # Spinner panel right
        control_spi = [
            [sg.Checkbox('Use Recipe', True, s=size, k='-RECIPE-USE-', enable_events=True, font=(bd.font, bd.text_size), background_color=bd.bg_color)],
            [bd.getText("Load Recipe:", size, 'center')],
            [bd.getI('config/params.xlsx', (15,1), f"-RECIPE-FILE-", enable_events=True), 
            sg.FileBrowse(size=(8,1), font=(bd.font, bd.text_size), key=f"-RECIPE-BROWSE-", initial_folder='config')],
            [bd.getText('')],
            [bd.getP(), bd.getB("Load", size_B), bd.getB("Run", size_B), bd.getB("Stop", size_B), bd.getP()]
        ]
        control_spi = sg.Column(control_spi, background_color=bd.bg_color, justification='center', element_justification='left', vertical_alignment='top', size=(right_width, mid_height))
        spi.append(control_spi)

        layout = [[display_x, control_x], [bd.getText('')], [display_syr, control_syr], [bd.getText('')], spi]
        self.window = sg.Window("Para-Spin", layout, enable_close_attempted_event=True, resizable=True, finalize=True, icon='icon.ico')
        return

    def gui_loop(self, paths={}):
        """
        Run a loop to keep GUI window open
        - paths: dict of paths to save output
        """
        update_position = True
        update_spinner = [True for _ in self.setup.spinners]
        movement_buttons = {}
        for displacement in ['-10', '-1', '-0.1', '+0.1', '+1', '+10']:
            movement_buttons[f'X{displacement}'] = float(displacement)

        self.disable_interface(True)
        for key, ele in self.window.key_dict.items():
            if key in ('Load', 'Run', 'Stop', "-RECIPE-FILE-", "-RECIPE-BROWSE-"):
                ele.update(disabled=False)
            if '-SLIDE-' in key:
                ele.update(disabled=True)
        
        while True:
            event, values = self.window.read(timeout=30)
            ## 0. Exit loop
            if event in ('Ok', WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT, None):
                write_log(log_output, self.connects_df)
                self.save_current_state()
                break
            
            ## 00. Toggle between using recipe
            if event == '-RECIPE-USE-':
                if values['-RECIPE-USE-']:
                    self.disable_interface(True)
                    for key, ele in self.window.key_dict.items():
                        if key in ('Load', 'Run', 'Stop', "-RECIPE-FILE-", "-RECIPE-BROWSE-"):
                            ele.update(disabled=False)
                else:
                    self.disable_interface(False)
                    for key, ele in self.window.key_dict.items():
                        if key in ('Load', 'Run', 'Stop', "-RECIPE-FILE-", "-RECIPE-BROWSE-"):
                            ele.update(disabled=True)

            # 000. Update values
            if update_position:
                self.window['-X-POSITION-'].update(self.setup.current_x)
                self.window['-X-SLIDE-'].update(self.setup.current_x)
            for i in range(self.setup.n_syringes):
                syringe = self.setup.syringes[i]
                if syringe.reagent != '':
                    self.window[f'-REAGENT-{i}-'].update(syringe.reagent)
                self.window[f'-VOLUME-{i}-'].update(f"{syringe.volume} uL")
                self.window[f'-SYR-SLIDE-{i}-'].update(syringe.volume)
                if type(self.selected_syringe) == type(None) or syringe.order != self.selected_syringe.order:
                    self.window[f'-SYR-SELECT-{syringe.order}-'].update(button_color='#658268')
            for i in range(self.setup.n_spinners):
                spinner = self.setup.spinners[i]
                if type(self.selected_spinner) == type(None) or spinner.order != self.selected_spinner.order:
                    self.window[f'-SPI-SELECT-{spinner.order}-'].update(button_color='#658268')
                if update_spinner[i]:
                    self.window[f'-SPEED-{i}-'].update(spinner.speed)
                    duration = spinner.etc - time.time() if spinner.busy else 0
                    self.window[f'-DURATION-{i}-'].update(max(0, int(duration)))

            # Event handler #
            ## 1. XYZ control
            if event in ('<X>', 'Go To', 'Clear'):
                update_position = True
            ### 1.1 Home
            if event == '<X>':
                t = threading.Thread(target=self.setup.home, name=f'home')
                t.start()
                self.threads['home'] = t
            if self.setup.at_home:
                self.window['-X-POSITION-'].update(0)
                self.window['-X-SLIDE-'].update(0)
            ### 1.2 XYZ buttons
            if event in movement_buttons.keys():
                displacement = movement_buttons[event]
                self.setup.current_x = actuate.move_dispense_rel(self.setup.cnc, self.setup.current_x, displacement)
                self.setup.at_home = False
                update_position = True
            ### 1.3 Go To Position
            if event == 'Go To':
                x = float(values['-X-POSITION-'])
                displacement = x - self.setup.current_x
                self.setup.current_x = actuate.move_dispense_rel(self.setup.cnc, self.setup.current_x, displacement)
            if event == '-X-POSITION-':
                update_position = False

            ## 2. Alignment
            if event.startswith('-SYR-SELECT-'):
                order = int(event[-2])
                if type(self.selected_syringe) != type(None):
                    if self.selected_syringe.order != order:
                        self.selected_syringe = self.setup.syringes[order]
                        self.window[f'-SYR-SELECT-{order}-'].update(button_color='black')
                    else:
                        self.selected_syringe = None
                        self.setup.aligning -= 1
                else:
                    self.selected_syringe = self.setup.syringes[order]
                    self.window[f'-SYR-SELECT-{order}-'].update(button_color='black')
                    self.setup.aligning += 1
            
            if event.startswith('-SPI-SELECT-'):
                order = int(event[-2])
                update_spinner[order] = True
                if type(self.selected_spinner) != type(None):
                    if self.selected_spinner.order != order:
                        self.selected_spinner = self.setup.spinners[order]
                        self.window[f'-SPI-SELECT-{order}-'].update(button_color='black')
                    else:
                        self.window[f'-SPI-SELECT-{self.selected_spinner.order}-'].update(button_color=None)
                        self.selected_spinner = None
                        self.setup.aligning -= 1
                else:
                    self.selected_spinner = self.setup.spinners[order]
                    self.window[f'-SPI-SELECT-{order}-'].update(button_color='black')
                    self.setup.aligning += 1

            if type(self.selected_syringe) != type(None) and type(self.selected_spinner) != type(None) and self.setup.aligning>1:
                log_now(f'CNC align: syringe {self.selected_syringe.order} with spinner {self.selected_spinner.order}...')
                t = threading.Thread(target=self.setup.align, name=f'align', args=(self.selected_syringe.offset, self.selected_spinner.position))
                t.start()
                self.threads['align'] = t
                self.setup.aligning = -1
            if not self.setup.aligning:
                self.selected_syringe, self.selected_spinner = None, None

            ## 3. Syringe control
            if event in ('Aspirate', 'Dispense', 'Fill', 'Empty'):
                try:
                    volume = float(values['-SYR-VOLUME-'])
                except:
                    volume = 0
                if values['-ALL-SYR-']:
                    def batch_syringe(eve, vol):
                        for syringe in self.setup.syringes:
                            if eve == 'Aspirate':
                                syringe.aspirate(vol)
                            elif eve == 'Dispense':
                                syringe.dispense(vol)
                            elif eve == 'Fill':
                                syringe.fill('', vol)
                            elif eve == 'Empty':
                                syringe.empty()
                        return
                    t = threading.Thread(target=batch_syringe, name=f'empty', args=(event, volume))
                    self.threads['batch'] = t
                    t.start()
                elif type(self.selected_syringe) != type(None):
                    if event == 'Aspirate':
                        t = threading.Thread(target=self.selected_syringe.aspirate, name=f'aspirate', args=(volume,))
                    elif event == 'Dispense':
                        t = threading.Thread(target=self.selected_syringe.dispense, name=f'dispense', args=(volume,))
                    elif event == 'Fill':
                        t = threading.Thread(target=self.selected_syringe.fill, name=f'fill', args=('', volume))
                    elif event == 'Empty':
                        t = threading.Thread(target=self.selected_syringe.empty, name=f'empty')
                    self.threads[event.lower()] = t
                    t.start()
                    self.selected_syringe = None

            ## 4. Spin control
            if event.startswith('-SPEED-') or event.startswith('-DURATION-'):
                order = int(event[-2])
                update_spinner[order] = False
            if event.startswith('-SPI-START-'):
                order = int(event[-2])
                spinner = self.setup.spinners[order]
                try:
                    s_spin = int(values[f'-SPEED-{order}-'])
                    t_spin = int(values[f'-DURATION-{order}-'])
                except:
                    s_spin, t_spin = 0, 0

                spinner.busy = True
                spinner.etc = time.time() + t_spin + 1
                t = threading.Thread(target=spinner.execute, name=f'spin_{spinner.order}', args=(0, s_spin, t_spin))
                t.start()
                self.spin_threads.append(t)
                update_spinner[order] = True
                for key in (f'-SPEED-{order}-', f'-DURATION-{order}-', f'-SPI-START-{order}-'):
                    self.window[key].update(disabled=True)

            ## 5. Recipe control
            if event == 'Load':
                params_filename = values['-RECIPE-FILE-']
                self.receive_plans(params_filename, spin_only_mode=SPIN_ONLY)
                try:
                    check_again = False
                    self.assign_plans(['A','B','C','D'])
                    if self.check_setup():
                        print('Plans ok!')
                        pop.notif("Ready to fill?")
                        t = threading.Thread(target=self.prepare_setup, name=f'prepare_setup', args=(MANUAL_FILL, True))
                        t.start()
                        self.threads['prepare_setup'] = t
                        self.window['-Load-'].update(disabled=True)
                    else:
                        check_again = True
                finally:
                    if check_again:
                        print('Check config / params again!')

            elif event == 'Run':
                pop.notif("Ready to proceed?")
                t = threading.Thread(target=self.run_experiment, name=f'run_experiment', args=(None, 'scanning'))
                t.start()
                self.threads['run_experiment'] = t
                self.window['Run'].update(disabled=True)
                self.window['-RECIPE-USE-'].update(disabled=True)

            elif event == 'Stop':
                self.stop = True
                self.unfreeze = True

            if self.unfreeze:
                self.disable_interface(False)
                self.window['-RECIPE-USE-'].update(disabled=False)
                self.unfreeze = False

        return

    def run_program(self, paths={}, maximize=False):
        """
        Run program based on build_window and defined gui_loop
        - paths: dict of paths to save output
        - maximize: whether to maximize window
        """        
        self.build_window()
        self.window.Finalize()
        if maximize:
            self.window.Maximize()
        self.window.bring_to_front()
        self.gui_loop(paths)
        self.window.close()
        return

    def assign_plans(self, plans):
        '''
        Assign the steps to the respective spinners
        - plans: list of plan labels for the spinners in order

        Returns: None
        '''
        if len(plans) != self.setup.n_spinners:
            print('Check plan assignment!')
            return
        for n, plan in enumerate(plans):
            df = self.steps_df[self.steps_df.plan.str.contains(plan)].copy()
            df.sort_values(by='order', axis=0, inplace=True)
            df.reset_index(inplace=True, drop=True)
            self.assignment.append([self.setup.spinners[n], df])
        return

    def calibrate_syringe(self, syringe_num=0):
        """Syringe volume calibration"""
        syringe = self.setup.syringes[syringe_num]
        test_sequence = 'baaadaddaaddd'
        test_vol = 500
        syringe.prev_action = ''
        for c in test_sequence:
            m = 1
            if c == 'b':
                prev_c = c
                continue
            if c == 'a':
                if prev_c == 'b':
                    m = 1
                if prev_c == 'a':
                    m = 1
                if prev_c == 'd':
                    m = 1
                print('Aspirate')
                syringe.aspirate(test_vol*m)
            if c == 'd':
                if prev_c == 'a':
                    m = 1
                if prev_c == 'd':
                    m = 1
                print('Dispense')
                syringe.dispense(test_vol*m, force_dispense=True)
            input('Ready for next?')
            prev_c = c
        syringe.dispense(test_vol*3, force_dispense=True)
        return

    def check_overrun(self, start_time, timeout):
        '''
        Check whether time has been overrun
        - start_time: start of experiment
        - timeout: max time allowed

        Returns: bool
        '''
        if timeout!=None and time.time() - start_time > timeout:
            for thread in self.spin_threads:
                thread.join(timeout=300)
            log_now(f'Exceeded runtime of {timeout}s', True)
            return True
        return False

    def check_positions(self):
        '''
        Check the alignment of the syringes and spinners
        
        Returns: None
        '''
        for spinner in self.setup.spinners:
            if spinner.order == 0:
                for syringe in self.setup.syringes:
                    log_now(f'CNC align: syringe {syringe.order} with spinner {spinner.order}...')
                    self.setup.align(syringe.offset, spinner.position)
                    # input('Ready for next?')
                    # pop.notif('Ready for next?')
                continue
            syringe = self.setup.syringes[-1]
            log_now(f'CNC align: syringe {syringe.order} with spinner {spinner.order}...')
            self.setup.align(syringe.offset, spinner.position)
            # input('Ready for next?')
            # pop.notif('Ready for next?')
        self.setup.align(0, self.setup.dump_position)
        return

    def check_setup(self):
        '''
        Checks the setup of the variables, such as number of spin positions with spin connections, and number syringes with number of reagents

        Returns: None
        '''
        if self.setup.n_spins != self.setup.n_spinners:
            print('Ensure number of spin addresses and spin positions are equal!')
            return False
        if len(self.syringes_df.order.to_list()) != len(self.syringes_df.reagent.to_list()):
            print('Ensure number of assigned syringes and reagents are equal!')
            return False
        if not set(self.steps_df.reagent.values).issubset(set(self.syringes_df.reagent.values)):
            print('Ensure reagents in steps are in syringes!')
            return False
        return True

    def disable_interface(self, disable=True):
        for _, ele in self.window.key_dict.items():
            if 'Button' in str(type(ele)) or 'Input' in str(type(ele)):
                ele.update(disabled=disable)
        if disable:
            self.window['Stop'].update(disabled=False)
        return

    def give_instructions(self, spinner, steps, new_thread=True, rest_home=True):
        '''
        Queue / send instructions to spinner
        - spinner: relevant Spinner object
        - steps: dataframe of remaining steps
        - new_thread: whether to start a new thread
        - rest_home: whether to send cnc arm to home during rest

        Returns: None
        '''
        syringe = self.setup.syringes[self.setup.reagents.index(steps.at[0, 'reagent'])]
        args = steps.loc[0, ['volume', 'soak_time', 'spin_speed', 'spin_time']].values
        steps.drop(0, axis=0, inplace=True)
        steps.reset_index(inplace=True, drop=True)
        thread = self.setup.coat(spinner, syringe, *args, new_thread=new_thread, rest_home=rest_home)
        self.spin_threads.append(thread)
        time.sleep(0.05)
        return

    def prepare_setup(self, manual=True, prewet=True):
        '''
        Prepare the setup by filling the syringes
        - manual: supervised filling of syringes

        Returns: None
        '''
        orders = self.syringes_df.order.to_list()
        reagents = self.syringes_df.reagent.to_list()
        volumes = [0 for _ in self.syringes_df.reagent.to_list()]

        # Check if there are enough reagent volumes for run
        req_vol_df = self.steps_df.iloc[:,:4].copy()
        req_vol_df['req_volume'] = [len(row['plan'])*row['volume'] for _, row in req_vol_df.iterrows()]
        req_vol_df = req_vol_df.groupby('reagent')['req_volume'].sum().reset_index()
        for _, row in req_vol_df.iterrows():
            idx = reagents.index(row['reagent'])
            if self.setup.syringes[idx].volume >= row['req_volume']:
                volumes[idx] = 0
                continue
            volumes[idx] = max(0, max(volumes[idx], row['req_volume']) - self.setup.syringes[idx].volume)
        
        # Notify and log fill order
        fill_order = []
        temp_fill_order = FILL_ORDER
        if len(temp_fill_order) != len(volumes):
            temp_fill_order = [s for s in range(len(volumes))]
        for n in temp_fill_order:
            vol = volumes[n]
            if vol:
                fill_order.append(f'{reagents[n]} ({vol}uL)')
        fill_msg = 'Filling in this order: ' + ', '.join(fill_order)
        log_now(fill_msg, True)
        time.sleep(1)

        self.setup.fill_syringes(orders, reagents, volumes, manual, prewet=prewet, spin_only_mode=self.spin_only_mode)
        return

    def receive_plans(self, params_file, spin_only_mode=False):
        '''
        Receives new parameters for syringe fill volumes and steps, and reset assignment and spin_threads
        - dfs: pd.read_excel(params.xlsx)

        Return: None
        '''
        dfs = pd.read_excel(params_file, None)
        self.syringes_df = self.syringes_df.merge(dfs['syringes'], on='order')
        self.steps_df = dfs['steps']
        self.assignment = []
        self.spin_threads = []
        self.spin_only_mode = spin_only_mode
        return

    def reset_setup(self, manual=True, home_only=True, default_home=True):
        '''
        Return the setup to its initial positions and states
        - manual: supervised emptying of syringes
        - home_only: whether to only send cnc arm to home position, without emptying syringes

        Returns: None
        '''
        log_now('Resetting!', True)
        if not home_only:
            self.setup.empty_syringes(self.syringes_df.order.to_list(), manual)
        actuate.run_solenoid(self.setup.pump, 9)
        actuate.run_pump(self.setup.pump, 0)
        if default_home:
            self.setup.home()
        else:
            log_now(f'CNC align: move to rest position...')
            self.setup.align(0, self.setup.dump_position)
        self.save_current_state()
        log_now('Back home!', True)
        return

    def run_experiment(self, timeout=None, mode='scanning'):
        '''
        Run the experiment
        - timeout: max time before halting (in s)
        - mode:
            - 'preempt': moves cnc arm to spinner with earliest estimated completion time while it is busy
            - 'scanning': continuously checks which spinner is free before moving cnc arm
            - 'sequential': non-parallel excecution

        Returns: None
        '''
        start_time = time.time()
        try:
            print('\n=== START ===')
            while not all([spinner.complete for spinner in self.setup.spinners]):
                time.sleep(0.05)
                if mode == 'preempt':
                    self.scheduler_preempt()
                elif mode == 'scanning':
                    self.scheduler_scanning()
                else:
                    self.scheduler_sequential(start_time, timeout)
                
                # Timeout break or force stop
                if self.check_overrun(start_time, timeout) or self.stop:
                    self.stop = False
                    break
            
            total_time_s = round(time.time() - start_time)
            m, s = divmod(total_time_s, 60)
            h, m = divmod(m, 60)
            log_now(f'Experiment complete! ({int(h):02}hr {int(m):02}min {int(s):02}sec)', True)
        finally:
            self.reset_setup(manual=True, home_only=True, default_home=False)
            for thread in self.spin_threads:
                thread.join(timeout=180)
            tool_log = write_log(log_output, self.connects_df)
            print('=== END ===')
            gantt_plotter(log_output, tool_log, show_plot=True, save_plot='html')
            gantt_plotter(log_output, tool_log, show_plot=False, save_plot='svg')
            self.unfreeze = True
        return

    def save_current_state(self, reset=False):
        '''
        Save the current state of the syringe volumes and cnc arm position
        - reset: whether to reset the volumes in syringes and position of cnc arm

        Returns: list of strings
        '''
        state_log = []
        if reset:
            self.setup.current_x = 0
        for syringe in self.setup.syringes:
            if reset:
                syringe.volume = 0
            state_log.append(f'syringe_{syringe.order}: {syringe.volume}')
        state_log.append(f'cnc_align: {self.setup.current_x}')
        with open('logs/save_state.txt', 'w') as f:
            for line in state_log:
                f.write(line + '\n') 
        return state_log
    
    def scheduler_preempt(self):
        '''
        Scheduler that preempts the next available spinner and moves cnc arm in anticipation

        Returns: None
        '''
        for spinner, steps in self.assignment:
            if spinner.busy:
                continue
            elif len(steps) == 0:
                spinner.complete = True
                spinner.etc = 0 
                continue
            else:
                self.give_instructions(spinner, steps, rest_home=False)
        
        if all([spinner.busy for spinner in self.setup.spinners]):
            next_spinner = None
            for spinner, steps in self.assignment:
                if spinner.etc == 0:
                    continue
                elif next_spinner == None:
                    next_spinner = spinner
                    next_steps = steps
                if spinner.etc < next_spinner.etc:
                    next_spinner = spinner
                    next_steps = steps
            
            if next_spinner != None and len(next_steps):
                if min([spinner.etc for spinner in self.setup.spinners if spinner.etc!=0]) > time.time() + 5:
                    self.setup.prime_syringes()
                self.give_instructions(next_spinner, next_steps, rest_home=False)
        return

    def scheduler_scanning(self):
        '''
        Scheduler that scans for the next available spinner and moves cnc arm once spinner is freed up

        Returns: None
        '''
        for spinner, steps in self.assignment:
            if spinner.busy:
                continue
            elif len(steps) == 0:
                spinner.complete = True
                spinner.busy = True
                continue
            else:
                self.give_instructions(spinner, steps, rest_home=False)
        
        if all([spinner.busy for spinner in self.setup.spinners]):
            if self.setup.current_x != self.setup.dump_position:
                log_now(f'CNC align: move to rest position...')
                self.setup.align(0, self.setup.dump_position)
                if min([spinner.etc for spinner in self.setup.spinners if spinner.etc!=0]) > time.time() + 5:
                    self.setup.prime_syringes()
        return

    def scheduler_sequential(self, start_time, timeout):
        '''
        Scheduler that performs all steps sequentially (i.e. non-parallel)
        - start_time: start time for experiment
        - timeout: max time before halting (in s)

        Returns: None
        '''
        for spinner, steps in self.assignment:
            while len(steps):
                self.give_instructions(spinner, steps, new_thread=False)
                self.setup.prime_syringes()

                # Timeout break
                if self.check_overrun(start_time, timeout):
                    return
            spinner.complete = True
        return
    

# %%
