# %%
import time

class Actuate:
    def __init__(self, mute_debug=False):  
        self.mute_debug = mute_debug
    def run_pump(self, mcu, speed):
        """
        Relay instructions to pump.
        - mcu: serial connection to pump
        - speed: speed of pump of rotation
        """
        try:
            mcu.write(bytes("{}\n".format(speed), 'utf-8'))
        except AttributeError:
            pass
        
    def run_solenoid(self, mcu, state):
        """
        Relay instructions to valve.
        - mcu: serial connection to pump
        - state: valve channel
            - -1 to -8   : open specific valve
            - 1 to 8     : close specific valve
            - 9          : close all valves
        """
        try:
            mcu.write(bytes("{}\n".format(state), 'utf-8'))
        except AttributeError:
            pass
    
    def dispense(self, mcu, pump_speed, prime_time, drop_time, channel):
        """
        Dispense (aspirate) liquid from (into) syringe.
        - mcu: serial connection to pump
        - pump_speed: speed of pump of rotation
            - <0    : aspirate
            - >0    : dispense
        - prime_time: time to prime the peristaltic pump
        - drop_time: time to achieve desired volume
        - channel: valve channel
        """
        
        run_time = prime_time + drop_time
        interval = 0.1
        
        starttime = time.time()
        self.run_solenoid(mcu, -channel)
        self.run_pump(mcu, pump_speed)
        
        while(True):
            time.sleep(0.001)
            if (interval <= time.time() - starttime):
                self.printer(run_time - interval)
                interval += 0.1
            if (run_time <= time.time() - starttime):
                self.printer(time.time() - starttime)
                break
        
        starttime = time.time()
        interval = 0.1
        self.run_solenoid(mcu, -channel)
        self.run_pump(mcu, -abs(pump_speed))

        while(True):
            time.sleep(0.001)
            if (interval <= time.time() - starttime):
                self.printer(prime_time - interval)
                interval += 0.1
            if (prime_time <= time.time() - starttime):
                self.printer(time.time() - starttime)
                self.run_pump(mcu, 10)
                self.run_solenoid(mcu, channel)
                break


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

