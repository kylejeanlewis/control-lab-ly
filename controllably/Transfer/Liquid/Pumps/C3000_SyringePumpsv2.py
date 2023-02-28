"""
Class object to control the Tricontinent C-Series Syringe Pumps

Author: Aniket Chitre
Date: July 2022
"""

import serial
import time

# See configuration jumpers on manual pp.22
# J2: 1, 5 installed, J9: none installed on all pumps except last - 1,2 installed on final pump
# Followed RS-232 cabling diagram
# Pumps in series communicate over RS-485, hence no RS-485 termination jumpers on all but last pump


class C3000_pump:

    baud_rate = 9600    # communications rate - set by J2 jumper #4
    to = 1              # timeout
    pause_time = 2    # delay required between writing and reading to the serial object

    # Key strings for pump control
    beg_char = '/'      # Start of command
    end_char = '\r'     # End of command
    run = 'R'           # Run. Execute the command string. Not required for certain classes of commands - e.g., reporting commands
    init_CW = 'Z'       # Initialise with CW configuration - sets valve output to the right - see diagram pp. 50
    # Pump initialises by default in the "N0" normal increment mode - full stroke = 3000 increments

    valve_to_input = 'I'
    valve_to_output = 'O'
    valve_to_bypass = 'B'

    # Plunger moves at a start velocity and accelerates to a "top velocity" and decelerates back down - motion controlled by driver automatically
    set_start_vel = 'v'     # power-up default = 900 increment/sec, range: 1 - 1000
    set_top_vel = 'V'       # power-up default = 1400 increment/sec, range: 1 - 6000
    set_ramp_slopes = 'L'   # see pp. 66 - default: 14 (= 35,000 increment/s^2) - I think <L10> will be suitable (25,000 increment/s^2)
    # n.b. power-up defaults to fast - cause cavitation when using 1/16" tubing

    absolute_pos = 'A'  # range: 0 - 3000 - volume dispensed = displacement of plunger
    rel_pos_down = 'P'  # aspirate
    rel_pos_up = 'D'  # dispense

    syringe_vol = 2500  # uL
    max_N = 3000  # max number of increments for C3000

    # default start-up status prior to pump connection or initialisation
    con_status  = False
    init_status = False
    dose_cmd    = ''

    def __init__(self, port, address):
        self.ser = None
        self.port = port
        self.address = address

    def connect(self):
        self.ser = serial.Serial(port=self.port, baudrate=self.baud_rate, timeout=self.to)
        self.__setattr__('con_status', True)
        self.ser.close()    # close the connection, so another pump can be opened over the same COM port
        return self.con_status

    # all method calls enclosed with the serial port being opened and closed on the first and penultimate lines
    # crucial to avoid conflicts on port access

    def initialise(self):
        self.ser.open()
        init_str = self.beg_char + self.address + self.init_CW + self.run + self.end_char
        init_byt = init_str.encode('utf-8')
        self.ser.write(init_byt)
        self.__setattr__('init_status', True)
        self.ser.close()
        return self.init_status

    def prime(self, prime_cycles):
        self.ser.open()
        # g opens the loop - G closes the loop and prime_cycles is the num_iter around this loop
        # g IA3000 (set to input valve and fill the syringe fully) OA0 (empty syringe completely) G
        prime_str = self.beg_char + self.address + self.init_CW + \
                    self.set_start_vel + '50' + self.set_top_vel + '200' + 'L1' + \
                    'g' + \
                    self.valve_to_input + self.absolute_pos + '3000' \
                    + self.valve_to_output + self.absolute_pos + '0' + \
                    'G' + prime_cycles + self.run + self.end_char
        prime_byt = prime_str.encode('utf-8')
        self.ser.write(prime_byt)
        # checks whether the pump is busy executing a command or idle and accordingly prints when priming is complete
        status_check_str = self.beg_char + self.address + 'Q' + self.end_char
        status_check_byt = status_check_str.encode('utf-8')
        pump_status = 'busy'    # default value, during the command call, the pump is busy
        while pump_status == 'busy':
            self.ser.write(status_check_byt)
            time.sleep(0.2)
            pump_check = str(self.ser.read_until('').decode('utf-8'))
            #print(pump_check)
            if pump_check[2] == '@':    # manual pp.90 shows 3rd character = @ if the pump is busy, or ` if it is free
                pass
            elif pump_check[2] == '`':
                pump_status = 'free'    # only break the while loop once the task is complete and pump is idle again
        self.ser.close()
        return print("Priming of pump complete")

    # Titrating 8 mL formulations, experiments have shown ~ 500 uL acid/base is required for the titration
    # 2.5 mL capacity of the syringes, shall be sufficient

    def dose(self, vol, start_vel, top_vel):
        self.ser.open()
        # checks the current absolute position of the syringe to determine whether it needs to be filled again before dispensing
        pos_check_str = self.beg_char + self.address + '?' + self.end_char
        pos_check_byt = pos_check_str.encode('utf-8')
        self.ser.write(pos_check_byt)
        time.sleep(self.pause_time)     # pause time important for the instrument to have time to write back to the computer
        raw_out = self.ser.read_until().decode('utf-8')
        abs_pos = int(raw_out.split('`')[1].split('\x03')[0])   # studied the outputted string and splitting it according to return position

        vol_per_N = self.syringe_vol / self.max_N   # technically the finest resolution of the syringe --> 2500/3000 = 0.8333 uL
        num_N = int(vol / vol_per_N)     # compute the increments for the screw to traverse to dispense the desired volume

        if abs_pos >= 0.75 * self.max_N:    # if the syringe is more than 75% full directly dispense the desired amount
            disp_str = self.beg_char + self.address + self.set_start_vel + str(start_vel) + self.set_top_vel + str(top_vel) + 'L1' + \
                       self.rel_pos_up + str(num_N) + self.run + self.end_char
            disp_byt = disp_str.encode('utf-8')
            self.ser.write(disp_byt)
            self.__setattr__('dose_cmd', disp_str)

        else:   # refill the syringe if it is less than 75% full
            # crucial that all the desired commands are encoded into a single string (ran into a bug where trying to send 2 strings consecutively fails)
            asp_disp_str = self.beg_char + self.address + self.set_start_vel + str(start_vel) + self.set_top_vel + str(top_vel) + 'L1' + \
                           self.valve_to_input + self.absolute_pos + '3000' + self.valve_to_output + self.rel_pos_up + str(num_N) + \
                           self.run + self.end_char
            asp_disp_byt = asp_disp_str.encode('utf-8')
            self.ser.write(asp_disp_byt)
            self.__setattr__('dose_cmd', asp_disp_str)
        # checks whether the pump is busy or idle and complete with dispensing
        status_check_str = self.beg_char + self.address + 'Q' + self.end_char
        status_check_byt = status_check_str.encode('utf-8')
        pump_status = 'busy'
        while pump_status == 'busy':
            self.ser.write(status_check_byt)
            time.sleep(0.2)
            pump_check = str(self.ser.read_until('').decode('utf-8'))
            if pump_check[2] == '@':    # pp. 90 manual @ if busy, ` if free
                pass
            elif pump_check[2] == '`':
                pump_status = 'free'
        self.ser.close()

        if self.address =='1':
            return print(f"Dispensing {vol} uL base is complete")
        else:
            return print(f"Dispensing {vol} uL acid is complete")