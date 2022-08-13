# %%
# -*- coding: utf-8 -*-
"""
Created on 

@author: Chang Jie
"""
import os, sys
import numpy as np
import pandas as pd
from analysis import Onset
from plotting.plotters import plot_line, plot_kinked_fit_points, plot_add_point
print(f"Import: OK <{__name__}>")

PLANCKS_CONST = 6.626E-34
LIGHT_SPEED = 2.998E8
J_TO_EV = 1/1.602E-19


def process(all_paths, measurement_object, sample_ids):
    '''
    Main function to process the data and generate the visualisation
    - all_paths: dictionary of all the filepaths
    - measurement_object: the class used to handle the data
    - sample_ids: ids of interested samples

    Returns: measurement object (HSI) or None
    '''   
    if len(all_paths):
        sample_paths = {}
        for sample_id, paths in all_paths.items():
            path_list = [p for n, p in paths.items()]
            sample_paths[sample_id] = path_list[0]

        for name, path in sample_paths.items():
            batch = measurement_object(name, path, sample_ids)
            batch.plot()
            
        for sample in batch.collection.values():
            sample.plot()
        return batch
    else:
        print("No files found!")
    return


class HSI(Onset):
    """
    'HSI' class is a child class of 'Onset', and has additional methods to get the absorbance values and to generate plots.
    """
    def __init__(self, name, path, sample_ids):
        self.name = name
        self.folder = os.path.dirname(path)
        self.filepath = path
        self.sample_ids = sample_ids

        self.data = pd.read_table(self.filepath)
        cols = ['wavelength']+sample_ids
        col_map = {h: cols[i] for i, h in enumerate(self.data.columns.to_list())}
        self.data.rename(columns=col_map, inplace=True)

        if not os.path.exists(self.folder + '\\RESULTS'):
            os.makedirs(self.folder + '\\RESULTS')

        self.adf = pd.DataFrame()
        self.getAbsorbance()

        self.collection = {s: HSI_sample(s, self.folder, self.adf[['energy',s]]) for s in sample_ids}
        return


    def getAbsorbance(self):
        '''
        Calculates the absorbance values from the transmittance values in the output data

        Returns: dataframe of absorbance (pd.Dataframe)
        '''
        def get_abs(value):
            return 2 - np.log10(value)
        self.adf = self.data[(self.data['wavelength']>=420) & (self.data['wavelength']<=950)].copy()
        adf_x = (PLANCKS_CONST*LIGHT_SPEED*J_TO_EV*1E9) / self.adf.iloc[:, 0]
        adf_y = self.adf.iloc[:, 1:].applymap(get_abs)
        self.adf = pd.concat([adf_x, adf_y], axis='columns')
        self.adf.rename(columns={'wavelength': 'energy'}, inplace=True)
        return self.adf


    def plot(self, show_plot=True, save_plot=True):
        '''
        Generates an aggregated plot of all samples in the batch
        - show_plot: whether to display the plot
        - save_plot: whether to save the plot

        Returns: plot figure (plotly.graph_objects.figure)
        '''
        collection_names = '({})'.format(', '.join(self.sample_ids))
        save_details = {
            'folder': self.folder,
            'format': '\\HSI {}.html',
            'name': collection_names}
        fig = plot_line(self.adf, 'energy', self.sample_ids, 
            show_plot=show_plot, save_plot=save_plot, save_details=save_details)
        return fig


class HSI_sample(HSI):
    """
    'HSI' class is a child class of 'HSI', and has a modified 'plot' method.
    """
    def __init__(self, name, folder, adf):
        self.name = name
        self.folder = folder
        self.data = adf.copy()

        if not os.path.exists(self.folder + '\\RESULTS'):
            os.makedirs(self.folder + '\\RESULTS')

        self.find_intercept('energy', self.name, asc=False, ratio_base=5, ratio_slope=2)
        return


    def plot(self, show_plot=True, save_plot=True):
        '''
        Generates a plot of the data and the fitted lines and intercept
        - show_plot: whether to display the plot
        - save_plot: whether to save the plot

        Returns: plot figure (plotly.graph_objects.figure)
        '''
        fig = plot_kinked_fit_points(self.data, 'energy', self.name, self.name, 'energy (eV)', 'value', data_plot_type='line')
        save_details = {
            'folder': self.folder,
            'format': '\\{}_HSI.html',
            'name': self.name}
        fig = plot_add_point(fig, [self.intercept[0]], [self.intercept[1]],
            'intercept', ["{:.2f}".format(self.intercept[0])], 'markers+text', 'bottom center',
            show_plot=show_plot, save_plot=save_plot, save_details=save_details)
        return fig


# %%
def main():
    THERE = {'data': 'utils\\data'}
    here = os.getcwd()
    base = here.split('src')[0] + 'src'
    there = {k: '\\'.join([base,v]) for k,v in THERE.items()}
    for v in there.values():
        sys.path.append(v)
    from filesearch import get_basedir, locate_paths
    base_dir = get_basedir(r'\A STAR\QD cocktail party - General')
    main_dir = base_dir + r'\Characterisation\HSI'
    sample_ids_of_interest = ['G001', 'G002', 'G003', 'G004', 'G005', 'G006']
    
    batch_ids_of_interest = ['BG001']
    relevant_paths = locate_paths(main_dir, '', batch_ids_of_interest, 'file', '.txt')
    process(relevant_paths, HSI, sample_ids_of_interest)

# %%
if __name__ == '__main__':
    main()

# %%
