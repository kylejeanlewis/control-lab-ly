# %%
import sys
sys.path.append('../')
import os
import pandas as pd
from analysis import Onset
from plotting.plotters import plot_kinked_fit_points, plot_add_point

def main():
    from filesearch import get_basedir, locate_paths
    base_dir = get_basedir(r'\A STAR\QD cocktail party - General')
    main_dir = base_dir + r'\Characterisation\PESA'
    sample_ids_of_interest = ['Q025', 'Q026', 'Q027', 'Q028']
    
    relevant_paths = locate_paths(main_dir, '', sample_ids_of_interest, 'file', '.csv')
    process(relevant_paths, PESA)


def process(all_paths, measurement_object):
    '''
    Main function to process the data and generate the visualisation
    - all_paths: dictionary of all the filepaths
    - measurement_object: the class used to handle the data

    Returns: {sample_ids: PESA} or None
    ''' 
    if len(all_paths):
        sample_paths = {}
        for sample_id, paths in all_paths.items():
            path_list = [p for n, p in paths.items()]
            sample_paths[sample_id] = path_list[0]

        samples = {}
        for name, path in sample_paths.items():
            sample = measurement_object(name, path)
            sample.plot()
            samples[name] = sample
        return samples
    else:
        print("No files found!")
    return


class PESA(Onset):
    """
    'PESA' class is a child class of 'Onset', and has an extra method to generate plots.
    """
    def __init__(self, name, path):
        self.name = name
        self.folder = os.path.dirname(path)
        self.filepath = path
        
        self.data = pd.read_csv(self.filepath)
        headers = {
            'Energy[eV]': 'energy',
            'Counting Rate[cps]': 'cr',
            'CR^0.5[cps^0.5]': 'sqrt_cr',
            'Yield[cps]': 'yield',
            'Yield^0.5[cps^0.5]': 'sqrt_yield'}
        self.data.rename(columns=headers, inplace=True)

        if not os.path.exists(self.folder + '\\RESULTS'):
            os.makedirs(self.folder + '\\RESULTS')
        
        self.find_intercept('energy', 'sqrt_cr')
        return

    
    def plot(self, show_plot=True, save_plot=True):
        '''
        Generates a plot of the data and the fitted lines and intercept
        - show_plot: whether to display the plot
        - save_plot: whether to save the plot

        Returns: plot figure (plotly.graph_objects.figure)
        '''
        fig = plot_kinked_fit_points(self.data, 'energy', 'sqrt_cr', self.name, 'energy (eV)', 'counting rate^0.5')
        save_details = {
            'folder': self.folder,
            'format': '\\{}_PESA.html',
            'name': self.name}
        fig = plot_add_point(fig, [self.intercept[0]], [self.intercept[1]], 
            'intercept', ["{:.2f}".format(self.intercept[0])], 'markers+text', 'bottom center',
            show_plot=show_plot, save_plot=save_plot, save_details=save_details)
        return fig


if __name__ == '__main__':
    main()

# %%
