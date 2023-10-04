# %%
import init
from controllably.Measure.Electrical.Keithley import Keithley, programs
from controllably.Move.Cartesian import Primitiv
from controllably.Control.GUI.Basic import MoverPanel

from collections import namedtuple
import numpy as np
import pandas as pd
import plotly.express as px
import time

# %%
me = Primitiv('COM5')
gui = MoverPanel(me, axes='XYZ')
gui.runGUI()

# %%
source_drain = Keithley('192.168.1.101', name='source')
gate_drain = Keithley('192.168.1.102', name='gate')

# %%
source = source_drain.device
gate = gate_drain.device

# %%
Readings = namedtuple('Readings', ['sourceV','sourceI','gateV','gateI'])
all_readings = []

sourceV_range = np.linspace(-50,50,101)
gateV_range = [v for v in range(31)] + [-v for v in range(1,31)]

def measure_fet(sourceV_range, gateV_range):
    for gate_V in gateV_range:
        gate.reset()
        gate.sendCommands(['ROUTe:TERMinals FRONT'])
        gate.configureSource('voltage', limit=200, measure_limit=1e-6)
        gate.configureSense('current', limit=1e-6, four_point=False, count=1)
        gate.setSource(value=gate_V)
        gate.toggleOutput(on=True)
        # gate.run()
        gate.beep()

        source.reset()
        source.sendCommands(['ROUTe:TERMinals FRONT'])
        source.configureSource('voltage', limit=200, measure_limit=1e-6)
        source.configureSense('current', limit=1e-6, four_point=False, count=1)
        source.beep()

        for source_V in sourceV_range:
            source.setSource(value=source_V)
            source.toggleOutput(on=True)
            # source.run()
            time.sleep(0.1*1)
            
            out_source = source._query('READ? "defbuffer1", SOURce, READing')
            out_gate = gate._query('READ? "defbuffer1", SOURce, READing')
            out = f"{out_source},{out_gate}"
            reading = Readings(*[float(v) for v in out.split(',')])
            print(f"({int(gate_V)},{int(source_V)}) Current: {reading.sourceI}")
            all_readings.append(reading)
        
        time.sleep(3)
        source.beep()
        source.getErrors()
        gate.beep()
        gate.getErrors()
    
    return pd.DataFrame(all_readings)
# %%
