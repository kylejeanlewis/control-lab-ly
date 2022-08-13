# %%
import sys
sys.path.append('../')
import os
import pandas as pd
from analysis import Peaks
from plotting.plotters import plot_line_point

def main():
    from filesearch import get_basedir, locate_paths
    base_dir = get_basedir(r'\A STAR\QD cocktail party - General')
    main_dir = base_dir + r'\Characterisation\FTIR'
    sample_ids_of_interest = ['Q025', 'Q026', 'Q027', 'Q028']
    
    relevant_paths = locate_paths(main_dir, '', sample_ids_of_interest, 'file', '.csv')
    process(relevant_paths, FTIR, main_dir)


def process(all_paths, measurement_object, home_path):
    '''
    Main function to process the data and generate the visualisation
    - all_paths: dictionary of all the filepaths
    - measurement_object: the class used to handle the data
    - home_path: parent directory to which the overall plot can be saved

    Returns: dataframe of peaks and prominences (pd.Dataframe) or None
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

        collection_names = '({})'.format(', '.join(samples.keys()))
        full_df = pd.concat([s.bdf for s in samples.values()], ignore_index=True)
        peak_df = pd.concat([s.pdf for s in samples.values()], ignore_index=True)
        save_details = {
            'folder': home_path,
            'format': '\\FTIR peaks {}.html',
            'name': collection_names}
        plot_line_point(full_df, peak_df, 'wavenumber', 'corrected', names='sample', line_width=1,
                title='FTIR ' + collection_names, x_title='wavenumber', y_title='transmittance', 
                show_plot=True, save_plot=True, save_details=save_details)
        
        peaks = peak_df
        peaks.sort_values(by='wavenumber', inplace=True)
        return peaks
    else:
        print("No files found!")
    return


class FTIR(Peaks):
    """
    'FTIR' class is a child class of 'Peaks', and has an extra method of generating the plots.
    """
    def __init__(self, name, path):
        self.name = name
        self.folder = os.path.dirname(path)
        self.filepath = path
        
        self.data = pd.read_csv(self.filepath, names=['wavenumber', 'transmittance'])

        if not os.path.exists(self.folder + '\\RESULTS'):
            os.makedirs(self.folder + '\\RESULTS')

        self.bdf = self.data[(self.data['wavenumber']>=2000) & (self.data['wavenumber']<=3600)].copy()
        self.baseline_correction('transmittance', (2450,3250))
        self.locate_peaks()
        return

    
    def plot(self, show_plot=True, save_plot=True):
        '''
        Generates the plot
        - show_plot: whether to display the plot
        - save_plot: whether to save the plot

        Returns: plot figure (plotly.graph_objects.figure)
        '''
        save_details = {
            'folder': self.folder,
            'format': '\\{}_FTIR.html',
            'name': self.name}
        fig = plot_line_point(self.bdf, self.pdf, 'wavenumber', 'corrected', line_width=1,
            title=self.name, x_title='wavenumber', y_title='transmittance', 
            show_plot=show_plot, save_plot=save_plot, save_details=save_details)
        return fig


if __name__ == '__main__':
    main()

# %%
