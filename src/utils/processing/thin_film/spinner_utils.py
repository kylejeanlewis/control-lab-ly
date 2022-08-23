# %%
import time

class Actuate:
    def __init__(self, mute_debug=False):  
        self.mute_debug = mute_debug
        
    def run_speed(self, mcu, speed):
        """
        Relay instructions to spincoater.
        - mcu: serial connection to spincoater
        - speed: spin speed
        """
        try:
            mcu.write(bytes("{}\n".format(speed), 'utf-8'))
        except AttributeError:
            pass
        print("Spin speed: {}".format(speed))
        
    def run_spin_step(self, mcu, speed, run_time):
        """
        Perform timed spin step
        - mcu: serial connection to spincoater
        - speed: spin speed
        - run_time: spin time
        """
        starttime = time.time()
        
        interval = 1
        self.run_speed(mcu, speed)
        
        while(True):
            time.sleep(0.1)
            if (interval <= time.time() - starttime):
                self.printer(run_time - interval)
                interval += 1
            if (run_time <= time.time() - starttime):
                self.printer(time.time() - starttime)
                self.run_speed(mcu, 0)
                break
    