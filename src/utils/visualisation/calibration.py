# %% BROKEN
# -*- coding: utf-8 -*-
"""
Created on 

@author: Chang Jie
"""
import os, sys
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from plotting.plotters import plot_scatter, plot_add_line, plot_add_point

THERE = {'data': 'utils\\data'}
here = os.getcwd()
base = here.split('src')[0] + 'src'
there = {k: '\\'.join([base,v]) for k,v in THERE.items()}
for v in there.values():
    sys.path.append(v)

import database
print(f"Import: OK <{__name__}>")

# %%
def extract_data(all_paths, db_dir, update_db=True):
    '''
    Extracts data from raw text files retreived from surface profiler
    - all_paths: dictionary of all the filepaths
    - db_dir: database filepath
    - update_db: whether or not to write new entries into the database

    Returns: dataframe of Sample ID and Thickness (pd.Dataframe)
    '''
    print("Extracting data files...")
    def read_thickness(txt, encoding='utf-16-le'):
        thickness = 0
        if '_T' not in txt:
            return 0
        with open(txt, 'r', encoding=encoding) as file:
            lines = file.readlines()
            for line in lines:
                if line.startswith('\x00Height'):
                    thickness = line.replace('\x00Height\tHeight\t', '').replace('\tÅ\n', '')
        return abs(float(thickness))/10

    id_heights = []
    for idx, paths in all_paths.items():
        measurement_ids = []
        heights = []
        for _, p in paths.items():
            measurement_ids.append(p.replace('_results.txt', '').split('\\')[-1])
            heights.append(read_thickness(p))
        for h, height in enumerate(heights):
            if height == 0:
                continue
            date = measurement_ids[h].replace(idx+'_T', '')[:8]
            date = date[:4] + '-' + date[4:6] + '-' + date[6:]
            id_heights.append({
                'Measurement ID': measurement_ids[h],
                'Sample ID': idx,
                'Date measured': date,
                'Thickness': round(height, 3)
            })
    data = pd.DataFrame(id_heights)
    if update_db:
        params = data.to_dict('split')['data']
        db = database.SQLiteDB('../data/qd_database.db')
        command = """
            INSERT INTO thickness (measurement_id, sample_id, date_measured, thickness) 
            VALUES (?, ?, ?, ?) """
        db.update_database(command, params, close=True)
        
        # accdb = database.AccessDB(db_dir)
        # command = """
        #     INSERT INTO Thickness ([Measurement ID], [Sample ID], [Date measured], [Thickness (nm)]) 
        #     VALUES (?, ?, ?, ?) """
        # accdb.update_database(command, params, close=True)
    data.drop(columns=['Measurement ID', 'Date measured'], inplace=True)
    return data


def process(all_paths, measurement_object, sample_ids, desired_thickness, logs_path, force_fit=False):
    '''
    Main function to process the data and generate the visualisation
    - all_paths: dictionary of all the filepaths
    - measurement_object: the class used to handle the data
    - sample_ids: ids of interested samples
    - desired_thickness: target thickness of film in nm
    - logs_path: path of folder containing the database
    - force_fit: whether to force fit the curve to y = a*(x**-0.5)

    Returns: measurement_object (SpeedCollection)
    '''
    db = database.SQLiteDB('../data/qd_database.db')
    sdf = db.fetch_query('SELECT sample_id, qd_spin_speed FROM sample_overview', close=True)
    sdf.rename(columns={'sample_id': 'Sample ID', 'qd_spin_speed': 'QD spin speed (rpm)'}, inplace=True)
    db_dir = logs_path + r'\QD database.accdb'
    # sdf = fetch_query(db_dir, "SELECT [Sample ID], [QD spin speed (rpm)] FROM SampleOverview")
    sdf.set_index('Sample ID', drop=True, inplace=True)
    speed_map = sdf.loc[sample_ids, :].to_dict()['QD spin speed (rpm)']

    id_list = '({})'.format(', '.join(["'{}'".format(i) for i in sample_ids]))
    db.reconnect()
    data = db.fetch_query('SELECT sample_id, thickness FROM thickness WHERE sample_id in'+id_list, close=True)
    # data = fetch_query(db_dir, "SELECT [Sample ID], [Thickness (nm)] FROM Thickness WHERE [Sample ID] IN "+id_list)
    data.rename(columns={'sample_id': 'Sample ID', 'thickness': 'Thickness'}, inplace=True)
    if len(data) == 0:
        data = extract_data(all_paths, db_dir)
    if data['Sample ID'].nunique() != len(sample_ids):
        available_ids = data['Sample ID'].unique()
        extracted = [data]
        for idx in sample_ids:
            if idx not in available_ids:
                df = extract_data({idx: all_paths[idx]}, db_dir)
                extracted.append(df)
        data = pd.concat(extracted, axis=0, ignore_index=True)


    data['Speed'] = [speed_map[s] for s in data['Sample ID'].to_list()]
    data.dropna(inplace=True)
    speed_samples = measurement_object(data)
    speed_samples.fit_power_curve(force_fit)
    speed_samples.plot(show_outlier=False, show_plot=False)
    speed_samples.recommend_spin_speed(desired_thickness, show_plot=True)
    print("Recommended spin speed: {:,.0f}rpm".format(speed_samples.opt_speed))

    return speed_samples


class SpeedCollection(object):
    """
    'SpeedCollection' class contains methods to fit the curve from the data points, plot the curve,
    and recommend the appropriate spin speed for desired thickness.
    """
    def __init__(self, data):
        self.data = data
        median = self.data['Thickness'].median()
        self.data['outlier'] = [((t > 1.5*median) or (t < 0.5*median)) for t in self.data['Thickness']]

        self.opt_speed = 0
        self.target = 0
        self.smooth_x = [0]
        self.smooth_y = [0]
        self.popt = (1,1)
        return


    def fit_power_curve(self, force_fit=False):
        '''
        Fits the curve using the relation y = a*(x**b)
        - force_fit: whether to force b = -0.5

        Returns: ((b, a), x_values, y_values)
        '''
        def func(x, a, b):
            return a*(x**(b))
        def func_forced(x, a, b):
            b = -0.5
            return a*(x**(b))
        if force_fit:
            func = func_forced
        xdata = self.data[self.data['outlier']==False]['Speed']
        ydata = self.data[self.data['outlier']==False]['Thickness']
        popt, _ = curve_fit(func, xdata, ydata)
        if force_fit:
            popt = (popt[0], -0.5)
        self.popt = popt
        self.smooth_x = np.arange(xdata.min(), xdata.max(), 1)
        self.smooth_y = func(self.smooth_x, *popt)
        return self.popt, self.smooth_x, self.smooth_y


    def plot(self, show_recommended=False, show_outlier=False, show_plot=False):
        '''
        Generates the plot
        - show_recommended: whether to plot the recommended spin speed
        - show_outlier: whether to plot the outlier measurement values
        - show_plot: whether to display the plot

        Returns: plot figure (plotly.graph_objects.figure)
        '''
        line_name = 'Y = ({:.0f})*X^({:.3f})'.format(self.popt[0], self.popt[1])
        if show_outlier:
            fig = plot_scatter(self.data, 'Speed', 'Thickness', names='Sample ID',
                symbol='outlier', symbol_sequence=['circle', 'circle-open'])
            pass
        else:
            fig = plot_scatter(self.data[self.data['outlier']==False], 'Speed', 'Thickness', names='Sample ID')
        fig = plot_add_line(fig, self.smooth_x, self.smooth_y, name=line_name, show_plot=False)
        if show_outlier:
            fig.update_layout(title=line_name.format(self.popt[0], self.popt[1]), showlegend=False)
        if show_recommended:
            if self.opt_speed == 0 and self.target == 0:
                self.recommend_spin_speed()
            plot_add_point(fig, [self.opt_speed], [self.target], 
                'Recommended', ["{:,.0f}".format(self.opt_speed)], 'markers+text', 'bottom center',
                show_plot=False)
        
        if show_plot:
            fig.show()
        self.fig = fig
        return self.fig


    def recommend_spin_speed(self, desired_thickness=30, show_plot=False):
        '''
        Recommends the appropriate spin speed for the target thickness
        - desired_thickness: target thickness in nm
        - show_plot: whether to display the plot

        Returns: optimal speed (float)
        '''
        def inv_func(y, a, b):
            return (y/a)**(1/b)
        self.opt_speed = inv_func(desired_thickness, *self.popt)
        self.target = desired_thickness
        self.plot(show_recommended=True, show_plot=show_plot)
        return self.opt_speed

# %%
def main():
    from filesearch import get_basedir, locate_paths
    base_dir = get_basedir(r'\A STAR\QD cocktail party - General')
    main_dir = base_dir + r'\Characterisation\Profilometry'
    logs_dir = base_dir + r'\Experiment logs'
    sample_ids_of_interest = ['G001', 'G002', 'G003', 'G004']
    relevant_paths = locate_paths(main_dir, '', sample_ids_of_interest, 'file', '.txt')
    return process(relevant_paths, SpeedCollection, sample_ids_of_interest, 30, logs_dir, force_fit=False)

# %%
if __name__ == '__main__':
    sample = main()

# %%
