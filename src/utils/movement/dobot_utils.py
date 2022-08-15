# %% -*- coding: utf-8 -*-
"""
Created on Wed 2022 Jul 20 11:54:04

@author: cjleong
"""
import os, sys
import time
import math
import numpy as np
from dobot.dobot_api import dobot_api_dashboard, dobot_api_feedback, MyType

THERE = {'electrical': 'utils\\characterisation\\electrical'}
here = os.getcwd()
base = here.split('src')[0] + 'src'
there = {k: '\\'.join([base,v]) for k,v in THERE.items()}
for v in there.values():
    sys.path.append(v)

from sensorpal import SensorEIS
from keithley import KeithleyLSV
print(f"Import: OK <{__name__}>")

# %%
def decodeDetails(details):
    """
    Decode JSON representation of keyword arguments for Dobot initialisation
    - details: dictionary of keyword, value pairs
    """
    for k,v in details.items():
        if type(v) != dict:
            continue
        if "tuple" in v.keys():
            details[k] = tuple(v['tuple'])
        elif "array" in v.keys():
            details[k] = np.array(v['array'])
    return details


class Dobot(object):
    """
    Dobot class 
    - address: IP address of arm
    - home_position: position to home in arm coordinates
    - home_orientation: orientation to home
    - orientate_matrix: matrix to transform arm axes to workspace axes
    - translate_vector: vector to transform arm position to workspace position
    - scale: scale factor to transform arm scale to workspace scale
    """
    def __init__(self, address='192.168.2.8', home_position=(0,300,0), home_orientation=(0,0,0), orientate_matrix=np.identity(3), translate_vector=np.zeros(3), scale=1):
        self.address = address
        self.dashboard = None
        self.feedback = None

        # Vector that points from implement tip to tool holder
        self.implement_offset = (0,0,0)
        self.home_position = home_position
        self.home_orientation = home_orientation
        self.orientate_matrix = orientate_matrix
        self.translate_vector = translate_vector
        self.scale = scale
        
        self.current_x = 0
        self.current_y = 0
        self.current_z = 0
        self.coordinates = (self.current_x, self.current_y, self.current_z)
        self.orientation = (0,0,0)

        self.connect(address)
        self.home()
        pass

    def __delete__(self):
        self.shutdown()
        return

    def calibrationMode(self, tip_length=21):
        self.setImplementOffset((0,0,tip_length))
        return

    def isFeasible(self, coord):
        """
        Checks if specified coordinates is a feasible position for robot to access.
        """
        coord = tuple(np.array(coord) + np.array(self.implement_offset))
        x,y,z = coord

        j1 = round(math.degrees(math.atan(x/(y + 1E-6))), 3)
        if y < 0:
            j1 += (180 * math.copysign(1, x))
        if abs(j1) > 160:
            return False

        # if not -150 < z < 230:
        #     return False

        return True

    def connect(self, address):
        """
        Establish connection with robot arm.
        """
        try:
            self.dashboard = dobot_api_dashboard(address, 29999)
            self.feedback = dobot_api_feedback(address, 30003)

            self.reset()
            self.dashboard.User(0)
            self.dashboard.Tool(0)
            self.setSpeed(speed=100)
        except Exception as e:
            print(f"Unable to connect to arm at {address}")
            print(e)
        return
    
    def getOrientation(self):
        """"
        Read the current position and orientation of arm.
        """
        # self.feedback.WaitReply()
        return self.orientation

    def getPosition(self):
        """"
        Read the current position and orientation of arm.
        """
        # self.feedback.WaitReply()
        return self.coordinates
    
    def getSettings(self):
        arm = str(type(self)).split("'")[1].split('.')[1]
        param = ["address", "home_position", "home_orientation", "orientate_matrix", "translate_vector", "scale"]
        details = {k: v for k,v in self.__dict__.items() if k in param}
        for k,v in details.items():
            if type(v) == tuple:
                details[k] = {"tuple": list(v)}
            elif type(v) == np.ndarray:
                details[k] = {"array": v.tolist()}
        settings = {"arm": arm, "details": details}
        return settings
    
    def getWorkspacePosition(self, offset=True):
        return self.transform_vector_out(self.getPosition(), offset=offset)

    def home(self):
        """
        Home the robot arm.
        """
        # Tuck arm in to avoid collision
        self.moveCoordTo((0,225,75), self.home_orientation, offset=False)
        # Go to home position
        self.moveCoordTo(self.home_position, self.home_orientation)
        print("Homed")
        return

    def moveBy(self, vector):
        """
        Relative Cartesian movement, using workspace coordinates.
        """
        vector = self.transform_vector_in(vector)
        return self.moveCoordBy(vector)

    def moveTo(self, coord):
        """
        Absolute Cartesian movement, using workspace coordinates.
        """
        coord = self.transform_vector_in(coord, offset=True)
        return self.moveCoordTo(coord)

    def moveJointBy(self, relative_angle=(0,0,0,0,0,0)):
        """
        Relative joint movement. Angles in degrees.
        """
        relative_angle = relative_angle + (0,) * (6-len(relative_angle))
        try:
            self.feedback.RelMovJ(*relative_angle)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return

    def moveJointTo(self, absolute_angle=(0,0,0,0,0,0)):
        """
        Absolute joint movement. Angles in degrees.
        """
        absolute_angle = absolute_angle + (0,) * (6-len(absolute_angle))
        try:
            self.feedback.JointMovJ(*absolute_angle)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return

    def moveCoordBy(self, relative_coord=(0,0,0), orientation=(0,0,0)):
        """
        Relative Cartesian movement and tool orientation, using robot coordinates.
        """
        try:
            self.feedback.RelMovL(*relative_coord)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        
        # Rotate to orientation
        if any(orientation):
            self.moveJointBy((0,0,0,*orientation))

        # Update values
        self.current_x += relative_coord[0]
        self.current_y += relative_coord[1]
        self.current_z += relative_coord[2]
        self.coordinates = (self.current_x, self.current_y, self.current_z)
        self.orientation = tuple(np.array(orientation) + np.array(self.orientation))
        return

    def moveCoordTo(self, absolute_coord, orientation=(0,0,0), offset=True):
        """
        Absolute Cartesian movement and tool orientation, using robot coordinates.
        """
        absolute_arm_coord = tuple(np.array(absolute_coord) + np.array(self.implement_offset)) if offset else absolute_coord
        if not self.isFeasible(absolute_arm_coord):
            print(f"Infeasible coordinates! {absolute_arm_coord}")
            return
        
        try:
            self.feedback.MovJ(*absolute_arm_coord, *orientation)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        
        # Update values
        self.current_x, self.current_y, self.current_z = absolute_coord
        self.coordinates = absolute_coord
        self.orientation = orientation
        return

    def reset(self):
        """
        Clear any errors and enable robot.
        """
        try:
            self.dashboard.ClearError()
            self.dashboard.EnableRobot()
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return

    def rotateBy(self, angles):
        """
        Relative tool orientation.
        """
        return self.moveCoordBy(orientation=angles)

    def rotateTo(self, orientation):
        """
        Absolute tool orientation.
        """
        return self.moveCoordTo(self.coordinates, orientation)
    
    def setImplementOffset(self, implement_offset):
        self.implement_offset = implement_offset
        self.home()
        return

    def setSpeed(self, speed):
        """
        Setting the Global rate   
        speed: Rate value(Value range:1~100)
        """
        try:
            self.dashboard.SpeedFactor(speed)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return

    def shutdown(self):
        """
        Stop robot and close conenctions.
        """
        self.stop()
        try:
            self.dashboard.close()
            self.feedback.close()
        except (AttributeError, OSError):
            print("Not connected to arm!")

        self.dashboard = None
        self.feedback = None
        return

    def stop(self):
        """
        Stop and disable robot.
        """
        try:
            self.dashboard.ResetRobot()
            self.dashboard.DisableRobot()
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return

    def transform_vector_in(self, coord, offset=False, stretch=False):
        translate = self.translate_vector if offset else np.zeros(3)
        scale = self.scale if stretch else 1
        return tuple( np.matmul(self.orientate_matrix, (np.array(coord)-translate)/scale) )

    def transform_vector_out(self, coord, offset=False, stretch=False):
        translate = self.translate_vector if offset else np.zeros(3)
        scale = self.scale if stretch else 1
        return tuple( scale * np.matmul(np.linalg.inv(self.orientate_matrix), np.array(coord)) + translate )


# First-party implement attachments
class JawGripper(Dobot):
    """
    JawGripper class 
    - address: IP address of arm
    - home_position: position to home in arm coordinates
    - home_orientation: orientation to home
    - orientate_matrix: matrix to transform arm axes to workspace axes
    - translate_vector: vector to transform arm position to workspace position
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.implement_offset = (0,0,95)
        self.home()
        return

    def grab(self):
        # Close gripper
        try:
            self.dashboard.DOExecute(1,0)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return

    def release(self):
        # Open gripper
        try:
            self.dashboard.DOExecute(1,1)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return


class VacuumGrip(Dobot):
    """
    VacuumGrip class 
    - address: IP address of arm
    - home_position: position to home in arm coordinates
    - home_orientation: orientation to home
    - orientate_matrix: matrix to transform arm axes to workspace axes
    - translate_vector: vector to transform arm position to workspace position
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.implement_offset = (0,0,60)
        self.home()
        return

    def grab(self):
        # Suction on
        try:
            self.dashboard.DOExecute(1,1)
            time.sleep(3)
            self.dashboard.DOExecute(1,0)
            time.sleep(1)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return

    def release(self):
        # Suction off
        try:
            self.dashboard.DOExecute(2,1)
            time.sleep(0.5)
            self.dashboard.DOExecute(2,0)
            time.sleep(1)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return


# Third-party implement attachments
class Instrument(Dobot):
    """
    Instrument class 
    - address_sensor: serial address of attachment
    - address: IP address of arm
    - home_position: position to home in arm coordinates
    - home_orientation: orientation to home
    - orientate_matrix: matrix to transform arm axes to workspace axes
    - translate_vector: vector to transform arm position to workspace position
    """
    def __init__(self, address_sensor=None, **kwargs):
        super().__init__(**kwargs)
        self.sensor = None
        self.connect_sensor(address_sensor)
        return

    def connect_sensor(self, address_sensor):
        return


class ForceSense(Instrument):
    """
    ForceSense class 
    - address_sensor: serial address of attachment
    - address: IP address of arm
    - home_position: position to home in arm coordinates
    - home_orientation: orientation to home
    - orientate_matrix: matrix to transform arm axes to workspace axes
    - translate_vector: vector to transform arm position to workspace position
    """
    def __init__(self, address_sensor=('COM4', 115200), **kwargs):
        super().__init__(**kwargs)
        self.connect_sensor(address_sensor)
        self.setImplementOffset((0,0,0))
        self.home()
        return
    
    def connect_sensor(self, address_sensor):
        self.sensor = serial.Serial(*address_sensor)
        self.sensor.flushInput()
        return


class EISMeasure(Instrument):
    """
    EISMeasure class 
    - address_sensor: serial address of attachment
    - address: IP address of arm
    - home_position: position to home in arm coordinates
    - home_orientation: orientation to home
    - orientate_matrix: matrix to transform arm axes to workspace axes
    - translate_vector: vector to transform arm position to workspace position
    """
    def __init__(self, address_sensor='COM4', **kwargs):
        super().__init__(**kwargs)
        self.connect_sensor(address_sensor)
        self.setImplementOffset((0,0,0))
        self.home()
        return

    def configure(self, settings={}):
        return self.sensor.configure(settings)

    def connect_sensor(self, address_sensor):
        self.sensor = SensorEIS(f'{there_eis}\\Measurement_Battery Impedance.json', address=address_sensor)
        return

    def measure(self):
        return self.sensor.measure()

    def plot(self, sample_num=0, plot_type='nyquist'):
        return self.sensor.plot(sample_num, plot_type)
    
    def save(self, sample_num=0):
        return self.sensor.save(sample_num)

    def setName(self, sample_num=-1, name=''):
        return self.sensor.setName(sample_num, name)


class LSVMeasure(Instrument):
    """
    Keithley
    """
    def __init__(self, address_sensor=None, **kwargs):
        super().__init__(address_sensor, **kwargs)
        self.connect_sensor(address_sensor)
        self.setImplementOffset((0,0,0))
        self.home()
        return

    def connect_sensor(self, address_sensor):
        self.sensor = KeithleyLSV(address_sensor, 'sweep')
        return

    def measure(self, name):
        # bias = self.measure_bias()
        # margin = 0.5
        # lsv_df = self.measure_sweep((bias-margin, bias+margin, margin*200+1))
        # lsv_df.to_csv(f'{name}.csv')
        return self.sensor.measure(name)
    
    def measure_bias(self):
        keithley = self.sensor
        settings = [
            '*RST',
            'OUTP:SMOD HIMP',
            'SOUR:FUNC CURR',
            'SOUR:CURR 0',
            'SOUR:CURR:RANG 1',
            'SOUR:CURR:VLIM 20',
            
            'SENS:FUNC "VOLT"',
            'SENS:VOLT:RANG 20',

            'SENS:COUN 3',
            'TRAC:MAKE "biasdata", 100',

            'SOUR:CURR 0',
            'TRAC:CLE "biasdata"',
            'OUTP ON',
            'TRAC:TRIG "biasdata"'
        ]
        keithley.set_parameters(settings)
        volt = 0
        try:
            keithley.inst.write('TRAC:DATA? 1, 3, "biasdata", READ')
            volt = None
        except (AttributeError, OSError) as e:
            print(e)
        while volt is None:
            try:
                volt = keithley.inst.read()
            except (AttributeError, OSError) as e:
                print(e)
        self.outp = [float(v) for v in volt.split(',')]
        avg = round( sum(self.outp) / len(self.outp), 3)
        print(f'OCV = {avg}V')
        return avg

    def measure_sweep(self, volt_range=(np.nan, np.nan, np.nan)):
        keithley = self.sensor
        sweep = ', '.join(str(v) for v in volt_range)

        settings = [
            '*RST',
            'OUTP:SMOD HIMP',
            'SENS:FUNC "CURR"',
            'SENS:CURR:RANG:AUTO ON',
            'SENS:CURR:RSEN OFF',
            
            'SOUR:FUNC VOLT',
            'SOUR:VOLT:RANG 20',
            'SOUR:VOLT:ILIM 1',
            f'SOUR:SWE:VOLT:LIN {sweep}, 0.1, 1, BEST, OFF, ON',
            'INIT',
            '*WAI',
        ]
        keithley.set_parameters(settings)
        time.sleep(2*volt_range[2] / 5)

        settings = [f'TRAC:DATA? 1, {2*volt_range[2]-1}, "defbuffer1", SOUR, READ, REL']
        keithley.set_parameters(settings)
        self.outp = keithley.inst.read().split(',')
        keithley.inst.write('OUTP OFF')

        data = np.reshape(np.array(self.outp), (-1,3))
        df = pd.DataFrame(data, columns=['V', 'I', 't'], dtype=np.float64)
        df.plot('V', 'I')

        diff = df.diff()
        df['Q'] = df['I'] * diff['t']
        df['dQdV'] = df['Q'].diff() / df['V'].diff()
        df.plot('V', 'dQdV')
        return df


# %%
if __name__ == '__main__':
    robot = LSVMeasure('123')
    robot.measure('LSV_data_sample')
    bias = robot.measure_bias()
    margin = 0.5
    lsv_df = robot.measure_sweep((bias-margin, bias+margin, margin*200+1))
    lsv_df.to_csv('LSV_data_sample.csv')
# %%
if __name__ == '__main__':
    df = pd.read_csv('LSV_data_sample 1.csv')
    diff = df.diff()
    df['Q'] = df['I'] * diff['t']
    df['dQdV'] = df['Q'].diff() / df['V'].diff()
    px.line(df, 'V', ['I', 'dQdV'])
    df.to_csv('LSV_data_sample.csv')
# %%
