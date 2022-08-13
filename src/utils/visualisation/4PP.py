# %%
# -*- coding: utf-8 -*-
"""
Created on 

@author: Chang Jie
"""
import os, sys
import pandas as pd
from plotting.plotters import plot_line, plot_scatter
print(f"Import: OK <{__name__}>")

def process(all_paths, measurement_object, sample_ids):
    if len(all_paths):
        sample_ids = []
        sample_paths = []
        for sample_id, paths in all_paths.items():
            sample_ids.append(sample_id)
            sample_paths = sample_paths + [p for _, p in paths.items()]
        samples = {}
        sample_dfs = []
        for s, sample_dir in enumerate(sample_paths):
            df = pd.read_csv(sample_dir+'\\1.csv')
            df = df[['Ig', 'Vg']]
            df['sample_id'] = sample_ids[s]
            samples[sample_ids[s]] = df
            sample_dfs.append(df)
    sample_df = pd.concat(sample_dfs)
    fig = plot_scatter(
        sample_df, 'Ig', 'Vg', 
        '4PP measurement', 'I', 'V', 'sample_id',
        show_plot=True
    )
    fig.write_html(f"{main_dir}\\{' '.join(sample_ids)}.html")
    return samples, sample_df, fig

class FourProbe(object):
    def __init__(self) -> None:
        pass


# %%
def main():
    THERE = {'data': 'utils\\data'}
    here = os.getcwd()
    base = here.split('src')[0] + 'src'
    there = {k: '\\'.join([base,v]) for k,v in THERE.items()}
    for v in there.values():
        sys.path.append(v)
    from filesearch import get_basedir, locate_paths
    global main_dir
    base_dir = get_basedir(r'\A STAR\QD cocktail party - General')
    main_dir = base_dir + r'\Characterisation\Ender'
    sample_ids_of_interest = ['Q143_D', 'Q144_D', 'Q145_D', 'Q143_E', 'Q144_E', 'Q145_E']
    relevant_paths = locate_paths(main_dir, '', sample_ids_of_interest, 'folder')
    return process(relevant_paths, FourProbe, sample_ids_of_interest)

# %%
if __name__ == '__main__':
    out, out_df, figure = main()
    pass
# %%
