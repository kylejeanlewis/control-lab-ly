# %% -*- coding: utf-8 -*-
"""

"""
# Standard library imports
import cmath
import json
import math
import numpy as np
import os
import pandas as pd
import pkgutil
import time

# Third party imports
from impedance import preprocessing                     # pip install impedance
from impedance.models.circuits import CustomCircuit
from impedance.models.circuits.fitting import rmse
import plotly.express as px                             # pip install plotly-express
import plotly.graph_objects as go                       # pip install plotly
from plotly.subplots import make_subplots
import yaml                                             # pip install pyyaml

# Local application imports
from . import circuit_diagram_utils as cd
from . import eis_utils as eis
print(f"Import: OK <{__name__}>")

PACKAGE = __package__.split('.')[-1]
TEST_CIRCUITS_FILE = f"{PACKAGE}/eis_test_circuits.yaml"

class ImpedanceSpectrum(object):
    """
    ImpedanceSpectrum object holds the frequency and complex impedance data, as well as provides methods to fit the plot and identify equivalent components

    Args:
        data (pd.DataFrame): dataframe with 3 columns for Frequency, Real impedance, and Imaginary impedance
        circuit (str, optional): string representation of circuit. Defaults to ''.
        name (str, optional): sample name. Defaults to ''.
        instrument (str, optional): instrument from which the data is measured/obtained. Defaults to ''.
    """
    def __init__(self, data:pd.DataFrame, circuit='', name='', instrument=''):
        self.name = name
        self.f, self.Z, self.P = np.array([]), np.array([]), np.array([])
        self.Z_fitted, self.P_fitted = np.array([]), np.array([])
        
        self.circuit = None
        self.diagram = ''
        self.isFitted = False
        
        self.min_rmse = -1
        self.min_nrmse = -1
        self.x_offset = 0
        
        self._read_data(data, instrument)
        self._read_circuit(circuit)

        self.bode_plot = None
        self.nyquist_plot = None
        return
    
    def _read_circuit(self, circuit:str):
        """
        Load and read string representation of circuit

        Args:
            circuit (str): string representation of circuit
        """
        if len(circuit):
            self.circuit = CustomCircuit()
            self.circuit.load(circuit)
        return
    
    def _read_data(self, data, instrument=''):
        """
        Read data and circuit model from file

        Args:
            data (str, or pd.DataFrame): name of data file or pd.DataFrame
            instrument (str, optional): name of measurement instrument. Defaults to ''.

        Returns:
            pd.DataFrame: cleaned/processed dataframe
        """
        if type(data) == str:
            try:
                frequency, impedance = preprocessing.readFile(data, instrument)
                real, imag = impedance.real, impedance.imag
                df = pd.DataFrame({'Frequency': frequency,'Real': real,'Imaginary': imag})
            except Exception as e:
                print('Unable to read/load data!')
                print(e)
                return
        elif type(data) == pd.DataFrame:
            df = data
        else:
            print('Please load dataframe or data filename!')
            return
        
        if instrument.lower() == 'biologic_':
            df['Impedance magnitude [ohm]'] = df['abs( Voltage ) [V]'] / df['abs( Current ) [A]']
            
            polar = list(zip(df['Impedance magnitude [ohm]'].to_list(), df['Impedance phase [rad]'].to_list()))
            df['Real'] = [p[0]*math.cos(p[1]) for p in polar]
            df['Imaginary'] = [p[0]*math.sin(p[1]) for p in polar]
            
            df = df[['Frequency [Hz]', 'Real', 'Imaginary']].copy()
            df.columns = ['Frequency', 'Real', 'Imaginary']
            df.dropna(inplace=True)
            pass
        
        df['Frequency_log10'] = np.log10(df['Frequency'])
        self.f = df['Frequency'].to_numpy()
        self.Z = df['Real'].to_numpy() + 1j*df['Imaginary'].to_numpy()

        df['Magnitude'] = np.array([abs(z) for z in self.Z])
        df['Phase'] = np.array([cmath.phase(z)/cmath.pi*180 for z in self.Z])
        self.P = np.array([*zip(df['Magnitude'].to_numpy(), df['Phase'].to_numpy())])
        
        self.data_df = df
        return df

    def fit(self, loadCircuit='', tryCircuits={}, constants={}, test_file = TEST_CIRCUITS_FILE):
        """
        Fit the data to an equivalent circuit

        Args:
            loadCircuit (str, optional): json filename of loaded circuit. Defaults to ''.
            tryCircuits (dict, optional): dictionary of (name, circuit string) to be fitted. Defaults to {}.
            constants (dict, optional): dictionary of (component, value) for components with fixed values. Defaults to {}.
        """
        frequencies, complex_Z = preprocessing.ignoreBelowX(self.f, self.Z)
        circuits = []
        fit_vectors = []
        rmse_values = []
        print(self.name)
        data = self.data_df[self.data_df['Imaginary']<0]
        stationary = eis.analyse(data=data)
        complex_Z = complex_Z + self.x_offset

        if type(self.circuit) != type(None):
            circuits = [self.circuit]
        elif len(loadCircuit):
            self.circuit = CustomCircuit()
            self.circuit.load(loadCircuit)
            circuits = [self.circuit]
        else:
            # json_string = pkgutil.get_data(__name__, 'eis_tests.json').decode('utf-8')
            # test_circuits = json.loads(json_string)
            yml = pkgutil.get_data(__name__, test_file).decode('utf-8')
            test_circuits = yaml.safe_load(yml)
            
            circuits_dict = {c['name']: c['string'] for c in test_circuits['standard']}
            if len(test_circuits['custom']):
                for c in test_circuits['custom']:
                    circuits_dict[c['name']] = c['string']
            if len(tryCircuits):
                circuits_dict = tryCircuits
            circuits_dict = {k: (v, eis.generate_guess(v, *stationary, constants)) for k, v in circuits_dict.items()}
            circuits = [CustomCircuit(name=k, initial_guess=v[1][0], constants=v[1][1], circuit=v[0]) for k,v in circuits_dict.items()]

        jac = None
        weight_by_modulus = False
        x_intercept_idx = stationary[3][-1]
        frequencies_trim, complex_Z_trim = frequencies, complex_Z
        if x_intercept_idx < (0.4*len(self.data_df)):
            jac = '3-point'
        elif x_intercept_idx < (0.45*len(self.data_df)):
            frequencies_trim, complex_Z_trim = eis.trim(frequencies, complex_Z, x_intercept_idx)
            weight_by_modulus = True

        for circuit in circuits:
            # print(f'Trying {circuit.circuit}')
            circuit.fit(
                frequencies_trim, complex_Z_trim, 
                weight_by_modulus=weight_by_modulus, 
                jac=jac
            )
            fit_vector = circuit.predict(frequencies)
            rmse_value = rmse(complex_Z, fit_vector)
            fit_vectors.append(fit_vector)
            rmse_values.append(rmse_value)

        self.min_rmse = min(rmse_values)
        self.min_nrmse = self.min_rmse / np.mean(abs(complex_Z))
        index_min_rmse = np.argmin(np.array(rmse_values))
        self.circuit = circuits[index_min_rmse]
        self.Z_fitted = fit_vectors[index_min_rmse] - self.x_offset
        self.P_fitted = np.array([(abs(z), cmath.phase(z)/cmath.pi*180) for z in self.Z_fitted])
        print(f'RMSE: {self.min_rmse}\n', f'Normalised RMSE: {self.min_nrmse}\n')
        print(f'Circuit: {self.circuit.circuit}\n')
        self.isFitted = True
        return

    def getCircuitDiagram(self, verbose=True):
        """
        Get circuit diagram

        Args:
            verbose (bool, optional): whether to print diagram and circuit. Defaults to True.

        Returns:
            str: string drawing of circuit diagram
        """
        # simplifiedCircuit = CircuitDiagram.simplifyCircuit(self.circuit.circuit, verbose=verbose)
        # self.diagram = CircuitDiagram.drawCircuit(*simplifiedCircuit)
        simplifiedCircuit = cd.simplify_circuit(self.circuit.circuit, verbose=verbose)
        self.diagram = cd.draw_circuit(*simplifiedCircuit)
        if verbose and self.isFitted:
            print(self.diagram)
            print(self.circuit)
        else:
            print("Circuit not yet fitted!")
        return self.diagram

    @classmethod
    def plot(cls, plot_type=None, show_plot=True):
        """
        Create plots of the impedance data

        Args:
            plot_type (str, optional): plot type ('nyquist' / 'bode'). Defaults to None.
            show_plot (bool, optional): whether to show the plot. Defaults to True.

        Returns:
            None, or plotly.graph_objects.Figure: plotly figure object of drawn plot
        """
        if plot_type is None:
            plot_type = 'nyquist'
        if plot_type.lower() == 'nyquist' or len(plot_type) == 0:
            return cls.plotNyquist(show_plot)
        elif plot_type.lower() == 'bode':
            return cls.plotBode(show_plot)
        else:
            print('Plot type not available!')
        return

    def plotBode(self, show_plot=True):
        """
        Plots impedance data and fitted line (if any) in Bode plots

        Args:
            show_plot (bool, optional): whether to show the plot. Defaults to True.

        Returns:
            plotly.graph_objects.Figure: plotly figure object of drawn plot
        """
        big_fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('', ''),
            vertical_spacing = 0.02,
            shared_xaxes=True,
        )
        big_fig.update_layout(title_text=f'{self.name} - Bode plot')
        for r, y_axis in enumerate(('Magnitude', 'Phase')):
            fig = px.scatter(
                self.data_df, 'Frequency_log10', y_axis, color='Frequency_log10', title=self.name, color_continuous_scale='plasma'
            )
            if self.isFitted:
                y = np.array([p[r] for p in self.P_fitted])
                fig.add_trace(go.Scatter(
                    x=self.data_df['Frequency_log10'].to_numpy(),
                    y=y,
                    name=f'Fitted {y_axis}',
                    mode='lines',
                    marker={'color':'#47c969'},
                    showlegend=True
                ))
            for trace in range(len(fig["data"])):
                big_fig.append_trace(fig["data"][trace], row=r+1, col=1)
            big_fig.update_coloraxes(colorscale='plasma')
            big_fig.update_xaxes(title_text="", row=r+1, col=1)
            big_fig.update_yaxes(title_text=y_axis, row=r+1, col=1)
            if y_axis=='Phase':
                big_fig.update_yaxes(autorange='reversed', row=r+1, col=1)
                big_fig.update_xaxes(title_text="log(Frequency)", row=r+1, col=1)
        big_fig.update_layout(legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        ))
        big_fig.update_layout(coloraxis_colorbar=dict(title='Frequency', tickprefix='1.e'))
        big_fig.update_layout(hovermode="x")
        if show_plot:
            big_fig.show()
        self.bode_plot = big_fig
        return big_fig

    def plotNyquist(self, show_plot=True):
        """
        Plots impedance data and fitted line (if any) in Nyquist plots

        Args:
            show_plot (bool, optional): whether to show the plot. Defaults to True.

        Returns:
            plotly.graph_objects.Figure: plotly figure object of drawn plot
        """
        fig = px.scatter(
            self.data_df, 'Real', 'Imaginary', color='Frequency_log10', title=f'{self.name} - Nyquist plot',
            hover_data={'Real': True, 'Imaginary': True, 'Frequency': True, 'Frequency_log10': False}
        )
        if self.isFitted:
            fig.add_trace(go.Scatter(
                x=self.Z_fitted.real,
                y=self.Z_fitted.imag,
                name='Fitted',
                mode='lines',
                marker={'color':'#47c969'},
                showlegend=True
            ))
        fig.update_layout(legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ))
        fig.update_yaxes(autorange='reversed')
        fig.update_layout(coloraxis_colorbar=dict(title='Frequency', tickprefix='1.e'))
        fig.update_layout(hovermode="x")
        if show_plot:
            fig.show()
        self.nyquist_plot = fig
        return fig

    def save(self, filename='', folder=''):
        """
        Save data

        Args:
            filename (str, optional): filename to be used. Defaults to ''.
            folder (str, optional): folder to save to. Defaults to ''.
        """
        if len(filename) == 0:
            filename = time.strftime('%Y%m%d_%H%M ') + self.name
        if len(folder) == 0:
            folder = 'data'
        if not os.path.exists(folder):
            os.makedirs(folder)
        self.saveData(filename, folder)
        self.saveCircuit(filename, folder)
        self.savePlots(filename, folder)
        return

    def saveCircuit(self, filename='', folder=''):
        """
        Save circuit model to file

        Args:
            filename (str, optional): filename to be used. Defaults to ''.
            folder (str, optional): folder to save to. Defaults to ''.
        """
        try:
            json_filename = f'{folder}/{filename}.json'
            self.circuit.save(json_filename)
            with open(json_filename) as json_file:
                circuit = json.load(json_file)
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(circuit, f, ensure_ascii=False, indent=4)
            
            self.getCircuitDiagram(verbose=False)
            with open(f'{folder}/{filename}_circuit.txt', "w") as text_file:
                print(filename, file=text_file)
                print(self.diagram, file=text_file)
                print(f'RMSE: {self.min_rmse}', file=text_file)
                print(f'Normalised RMSE: {self.min_nrmse}', file=text_file)
                print(self.circuit, file=text_file)
        except AttributeError:
            print('Unable to save circuit model!')
        return

    def saveData(self, filename='', folder=''):
        """
        Save data to file

        Args:
            filename (str, optional): filename to be used. Defaults to ''.
            folder (str, optional): folder to save to. Defaults to ''.
        """
        try:
            freq, _ = preprocessing.ignoreBelowX(self.f, self.Z)
            preprocessing.saveCSV(f'{folder}/{filename}.csv', self.f, self.Z)
            preprocessing.saveCSV(f'{folder}/{filename}_fitted.csv', freq, self.Z_fitted)
        except ValueError:
            print('Unable to save fitted data!')
        return

    def savePlots(self, filename='', folder=''):
        """
        Save plots to file

        Args:
            filename (str, optional): filename to be used. Defaults to ''.
            folder (str, optional): folder to save to. Defaults to ''.
        """
        try:
            self.bode_plot.write_html(f'{folder}/{filename}_Bode.html')
            self.nyquist_plot.write_html(f'{folder}/{filename}_Nyquist.html')
        except AttributeError:
            print('Unable to save plots!')
        return
