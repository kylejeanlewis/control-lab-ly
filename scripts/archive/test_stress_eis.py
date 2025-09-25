# %%
import pandas as pd

from easy_biologic.base_programs import PEIS, GEIS
from controllably.Measure.Electrical.BioLogic import BioLogic
from leapfrog.Analyse.Data.Impedance import ImpedanceSpectrum

# %%
bio = BioLogic('192.109.209.128')
# %%
bio.loadProgram(PEIS)
# %%
"""PEIS"""
parameters = dict(
    voltage = 0.0,
    amplitude_voltage = 10E-3,
    initial_frequency=16E6,
    final_frequency = 10,
    frequency_number = 200,
    duration = 30
)
"""GEIS"""
# parameters = dict(
#     current = np.array([10E-3]),
#     amplitude_current = 1E-4,
#     initial_frequency = 100000,
#     final_frequency = 1,
#     frequency_number = 100,
#     duration = 30
# )
bio.measure(parameters=parameters, channel=[0,1])
# %%
eis = ImpedanceSpectrum(bio.buffer_df, instrument='Biologic')
eis.plot()
# %%
bio.program.save_data("vmp_test3_multichannel", by_channel=True)

# %%
bio.program.data
# %%
bio.buffer_df.to_csv(f"data/test_polymer_sample_20230810_recipe_2_t-10,3_1GHz.csv")
coin_cell = 10.75 # mm
# %%
import pandas as pd
import plotly.express as px
from leapfrog.Analyse.Data.Impedance import ImpedanceSpectrum

# %%
eis_files = {}
for i in (2,3,4,5,6):
    filename = f"data/test_polymer_sample_H4_t-10,{i}.csv"
    df = pd.read_csv(filename)
    eis = ImpedanceSpectrum(df, name=f"H4_t-10.{i}",instrument="Biologic")
    eis.df['run'] = i
    eis_files[i] = eis

# %%
big_df = pd.concat([e.df for e in eis_files.values()])
fig = px.scatter(big_df, x='Real', y='Imaginary', color='run')
fig['layout']['yaxis']['autorange'] = "reversed"
fig.show()

# %%
eis_files = {}
for i in (0,1):
    filename = f"vmp_test2_multichannel/ch-{i}.csv"
    df = pd.read_csv(filename)
    df.rename(columns={'Impendance phase': 'Impedance phase [rad]', 'Impendance_ce phase': 'Impedance_ce phase [rad]'}, inplace=True)
    df = df[df['Frequency [Hz]']<2500000]
    eis = ImpedanceSpectrum(df, name=f"ch-{i}",instrument="Biologic")
    eis.df['run'] = i
    eis_files[i] = eis
    eis.plot()
# %%
for i in (0,1):
    eis: ImpedanceSpectrum = eis_files[i]
    eis.circuit = None
    eis.fit()
    print(eis.circuit)
    eis.plot()
# %%
