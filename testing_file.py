import pandas as pd
from controllable.Analyse.Visualisation.visualisation_utils import VIZ

pd.options.plotting.backend = 'plotly'

df = pd.read_csv('DMA_test.csv', index_col=0)
df['Absolute Storage Modulus (MPa)'] = abs(df['Storage Modulus (MPa)'])
df['Absolute Loss Modulus (MPa)'] = abs(df['Loss Modulus (MPa)'])
df['Tan Delta'] = df['Absolute Loss Modulus (MPa)'] / df['Absolute Storage Modulus (MPa)'] 
df['freq_id'] = df.index % (len(df) / max(df['run']))

avg_df = df.groupby('freq_id').mean()
std_df = df.groupby('freq_id').std()
final_df = avg_df.join(std_df, rsuffix='_std')
final_df.drop(columns=[col for col in final_df.columns if col.startswith('run')], inplace=True)
final_df.reset_index(drop=True, inplace=True)

fig1 = final_df.plot('Frequency (Hz)', ['Absolute Storage Modulus (MPa)','Absolute Loss Modulus (MPa)'])
fig2 = final_df.plot('Frequency (Hz)', 'Tan Delta')
fig3 = final_df.plot('Frequency (Hz)', 'Frequency (Hz)')
figs = [fig1, fig2, fig3]*10

for fig in figs:
    VIZ.addGraph((fig))
    
VIZ.displayGraphs()
