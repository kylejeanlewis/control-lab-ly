# %% -*- coding: utf-8 -*-
"""
Impedance package documentation can be found at:
https://impedancepy.readthedocs.io/en/latest/index.html

Created on Fri 2022/06/18 09:00:00
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import cmath
import json
import math
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import pkgutil
from scipy.signal import argrelextrema
import time

# Third party imports
from impedance import preprocessing # pip install impedance
from impedance.models.circuits import CustomCircuit
from impedance.models.circuits.fitting import rmse, extract_circuit_elements
import plotly.express as px # pip install plotly-express
import plotly.graph_objects as go # pip install plotly
from plotly.subplots import make_subplots

# Local application imports
from .circuit_datatype import circuit_diagram
print(f"Import: OK <{__name__}>")

class ImpedanceSpectrum(object):
    """
    ImpedanceSpectrum object holds the frequency and complex impedance data, 
    as well as provides methods to fit the plot and identify equivalent components
    - data: pd.Dataframe with 3 columns for Frequency, Real, and Imaginary impedance
    - filename_data: filename of data
    - circuit: filename of circuit model
    - name: sample name
    """
    def __init__(self, data, circuit='', name='', instrument=''):
        self.name = name
        self.f, self.Z, self.P = np.array([]), np.array([]), np.array([])
        self.Z_fitted, self.P_fitted = np.array([]), np.array([])
        
        self.circuit = None
        self.diagram = ''
        self.isFitted = False
        
        self.min_rmse = -1
        self.min_nrmse = -1
        self.x_offset = 0
        
        self._readData(data, instrument)
        self._readCircuit(circuit)

        self.bode_plot = None
        self.nyquist_plot = None
        return
    
    def _analyse(self, order=4):
        data = self.data_df[self.data_df['Imaginary']<0].copy()
        data.sort_values(by='Frequency', ascending=False, inplace=True)
        y = data['Imaginary'].to_numpy() * (-1)
        x = data['Real'].to_numpy()
        f = data['Frequency'].to_numpy()

        def perp_bisector(pt1, pt2):
            mid = ((pt1[0]+pt2[0])/2, (pt1[1]+pt2[1])/2)
            slope = (pt1[1] - pt2[1]) / (pt1[0] - pt2[0])
            b = -1/slope
            a = mid[1] - b*mid[0]
            # print(f'slope, intercept: {b}, {a}')
            p1 = (0, a)
            p2 = mid
            
            A = (p1[1] - p2[1])
            B = (p2[0] - p1[0])
            C = (p1[0]*p2[1] - p2[0]*p1[1])
            return A, B, -C

        def intersection(L1, L2):
            D  = L1[0] * L2[1] - L1[1] * L2[0]
            Dx = L1[2] * L2[1] - L1[1] * L2[2]
            Dy = L1[0] * L2[2] - L1[2] * L2[0]
            if D != 0:
                x_i = Dx / D
                y_i = Dy / D
                return x_i,y_i
            else:
                return False

        def nudge_points(x_values, y_values):
            for i in range(1, len(x_values)-2):
                if x_values[i] > x_values[i+1]:
                    x_diff = x_values[i] - x_values[i+1]
                    x_values[i+1:] += x_diff

                    # y_x_1 = (y_values[i] - y_values[i-1]) / (x_values[i] - x_values[i-1])
                    # y_x_2 = (y_values[i+2] - y_values[i+1]) / (x_values[i+2] - x_values[i+1])
                    # avg_y_x = (y_x_1 + y_x_2) / 2
                    # y_diff = y_values[i+1] - y_values[i]
                    # x_corr = y_diff/avg_y_x
                    # x_values[i+1:] += x_corr
            return x_values

        # dydx = np.gradient(y)/np.gradient(x)
        # d2ydx2 = np.gradient(dydx)/np.gradient(x)
        # adydx = abs(dydx)

        # stat_pt = argrelextrema(y, np.less, order=order)
        # stat_pt = argrelextrema(adydx, np.less, order=order)
        # stat_pt = stat_pt[0]

        # mask_r = (dydx[list(stat_pt)] < 0.9) & (d2ydx2[list(stat_pt)] > -50)
        # mask_c = (dydx[list(stat_pt)] < 0.9) & (d2ydx2[list(stat_pt)] < -50)
        # min_idx = np.concatenate( (np.array( [np.argmin(x)] ), stat_pt[mask_r]) )
        # max_idx = stat_pt[mask_c]

        x = nudge_points(x,y)

        all_min_idx = argrelextrema(y, np.less, order=order)
        all_min_idx = np.concatenate( (np.array( [np.argmax(f)] ), all_min_idx[0]) )
        if y[-1] < np.mean(y[-1-order:-1]):
            all_min_idx = np.concatenate((all_min_idx, np.array( [np.argmin(f)] )) )
            pass
        window = 0.05 * max(x)
        min_idx = []
        for i, idx in enumerate(all_min_idx):
            if i == 0:
                min_idx.append(idx)
                continue
            pidx = all_min_idx[i-1]
            m_x, m_y = x[idx], y[idx]
            n_x, n_y = x[pidx], y[pidx]
            dist_from_prev = abs((m_x+1j*m_y) - (n_x+1j*n_y))
            if dist_from_prev >= window:
                min_idx.append(idx)
            elif m_y < n_y:
                min_idx.pop(-1)
                min_idx.append(idx)
            pass
        min_idx = np.array(min_idx)

        all_max_idx = argrelextrema(y, np.greater, order=order)[0]
        all_max_idx = all_max_idx[all_max_idx<max(min_idx)]
        max_idx = []
        right_min_x = max(x[list(min_idx)])
        for idx in all_max_idx:
            if x[idx] < right_min_x:
                max_idx.append(idx)
        max_idx = np.array(max_idx)
        if len(max_idx) == 0:
            max_idx = np.array([np.argmin(x)])
        
        try:
            top_idx = max_idx[0]
            bot_idx = min_idx[1]
            mid_idx = int((top_idx+bot_idx)/2)
            line1 = perp_bisector((x[top_idx], y[top_idx]), (x[mid_idx], y[mid_idx]))
            line2 = perp_bisector((x[bot_idx], y[bot_idx]), (x[mid_idx], y[mid_idx]))
            center = intersection(line1, line2)
            print(f'Center: {center}')


            r0_est = x[min_idx[1]] - 2*(x[min_idx[1]] - x[max_idx[0]])
            # if top_idx:
            #     r0_est = x[min_idx[1]] - 2*(x[min_idx[1]] - center[0])
            r0_est = min(r0_est, x[min_idx[0]])
        except IndexError:
            bot_idx = min_idx[-1]
            r0_est = x[min_idx[0]]
            min_idx = np.append(min_idx, [0])
        print(f'min: {min_idx}')
        print(f'max: {max_idx}')
        print(f'r0 est: {r0_est}')
        
        if r0_est < 0:
            # self.x_offset = int(abs(r0_est) + window)
            # x = x + self.x_offset
            # r0_est += int(abs(r0_est) + window)
            pass

        b,a = np.polyfit(x[bot_idx:], y[bot_idx:], deg=1)
        print(f'Warburg slope: {round(b,3)}')

        plt.scatter(x, y)
        plt.scatter(x[min_idx], y[min_idx])
        plt.scatter(r0_est, 0)
        plt.scatter(x[max_idx], y[max_idx])
        plt.show()

        # plt.scatter(x[abs(dydx)<5], dydx[abs(dydx)<5])
        # plt.scatter(x[min_idx], dydx[min_idx])
        # plt.scatter(0,0)
        # plt.scatter(x[max_idx], dydx[max_idx])
        # plt.show()

        # plt.scatter(x[abs(d2ydx2)<2], d2ydx2[abs(d2ydx2)<2])
        # plt.scatter(x[min_idx], d2ydx2[min_idx])
        # plt.scatter(0,0)
        # plt.scatter(x[max_idx], d2ydx2[max_idx])
        # plt.show()

        return f, x, y, min_idx, max_idx, r0_est, a ,b

    def _generateGuess(self, circuit_string, f, x, y, min_idx, max_idx, r0, a, b, constants={}):
        """
        Generate initial guesses from circuit string
        - circuit_string: string representation of circuit model
        Return: initial guess
        """
        init_guess = []
        new_constants = {}

        count_R = 0
        count_C = 0
        circuit_ele = extract_circuit_elements(circuit_string)
        for c in circuit_ele:
            if c in constants.keys():
                continue
            if 'R' in c:
                if c == 'R0':
                    guess = max(r0,0.01)
                else:
                    try:
                        guess = x[min_idx[count_R]] - x[min_idx[count_R-1]]
                        guess = max(guess,0)
                        if guess == 0:
                            guess = max(r0,0.1)
                    except IndexError:
                        guess = max(r0,0.1)
                init_guess.append(guess)
                count_R += 1
            if 'C' in c:
                try:
                    idx_c = max_idx[count_C]
                except IndexError:
                    idx_c = int((min_idx[0]+min_idx[1])/2)
                idx_r = min(min_idx[min_idx>idx_c])
                guess = 1 / (2*cmath.pi*x[idx_r]*f[idx_c])
                count_C += 1
                init_guess.append(guess)
            if 'CPE' in c:
                guess = 0.9
                init_guess.append(guess)
            if 'W' in c:
                guess = abs(b/a)
                init_guess.append(guess)
            if 'Wo' in c:
                guess = 200
                init_guess.append(guess)
        for k in constants.keys():
            if k in circuit_ele:
                new_constants[k] = constants[k]
        return init_guess, new_constants

    def _readCircuit(self, circuit):
        if len(circuit):
            self.circuit = CustomCircuit()
            self.circuit.load(circuit)
        return
    
    def _readData(self, data, instrument=''):
        """
        Read data and circuit model from file
        - data: name of file with data or pd.DataFrame
        - instrument: measurement instrument
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

    def fit(self, loadCircuit='', tryCircuits={}, constants={}):
        """
        Fits the data to an equivalent circuit
        - loadCircuit: json filename of loaded circuit
        - tryCircuits: dict of name, circuit string pairs to try fitting
        - constants: components for which to be given fixed values;
        """
        frequencies, complex_Z = preprocessing.ignoreBelowX(self.f, self.Z)
        circuits = []
        fit_vectors = []
        rmse_values = []
        print(self.name)
        stationary = self._analyse()
        complex_Z = complex_Z + self.x_offset

        def trim(f, Z, x, p=0.15):
            """
            Trim the 45-degree straight line to avoid overfit
            - f: frequencies
            - Z: complex impedances
            - x: final minimum point from ImpedanceSpectrum._analyse
            - p: proportion of data points to trim out

            Return: trimmed frequencies, trimmed complex impedances
            """
            f_trim = [f[0]]
            Z_trim = [Z[0]]
            end_idx = len(f) - 1 - x # flip index
            num_to_trim = int(p*len(f))
            step = (end_idx) % num_to_trim
            for i in range(len(f)):
                if i % step or i >= end_idx:
                    f_trim.append(f[i])
                    Z_trim.append(Z[i])
            f = np.array(f_trim)
            Z = np.array(Z_trim)
            return f, Z

        if type(self.circuit) != type(None):
            circuits = [self.circuit]
        elif len(loadCircuit):
            self.circuit = CustomCircuit()
            self.circuit.load(loadCircuit)
            circuits = [self.circuit]
        else:
            json_string = pkgutil.get_data(__name__, 'eis_tests.json').decode('utf-8')
            test_circuits = json.loads(json_string)
            circuits_dict = {c['name']: c['string'] for c in test_circuits['standard']}
            if len(test_circuits['custom']):
                for c in test_circuits['custom']:
                    circuits_dict[c['name']] = c['string']
            if len(tryCircuits):
                circuits_dict = tryCircuits
            circuits_dict = {k: (v, self._generateGuess(v, *stationary, constants)) for k, v in circuits_dict.items()}
            circuits = [CustomCircuit(name=k, initial_guess=v[1][0], constants=v[1][1], circuit=v[0]) for k,v in circuits_dict.items()]

        jac = None
        weight_by_modulus = False
        x_intercept_idx = stationary[3][-1]
        frequencies_trim, complex_Z_trim = frequencies, complex_Z
        if x_intercept_idx < (0.4*len(self.data_df)):
            jac = '3-point'
        elif x_intercept_idx < (0.45*len(self.data_df)):
            frequencies_trim, complex_Z_trim = trim(frequencies, complex_Z, x_intercept_idx)
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
        simplifiedCircuit = circuit_diagram.simplifyCircuit(self.circuit.circuit, verbose=verbose)
        self.diagram = circuit_diagram.drawCircuit(*simplifiedCircuit)
        if verbose and self.isFitted:
            print(self.diagram)
            print(self.circuit)
        else:
            print("Circuit not yet fitted!")
        return self.diagram

    def plot(self, plot_type='nyquist', show_plot=True):
        """
        Plots data (and fitted line, if any) in Nyquist plot
        - plot_type: choice of either Nyquist or Bode plots
        Return: fig
        """
        if plot_type.lower() == 'nyquist' or len(plot_type) == 0:
            return self.plotNyquist(show_plot)
        elif plot_type.lower() == 'bode':
            return self.plotBode(show_plot)
        else:
            print('Plot type not available!')
        return

    def plotBode(self, show_plot=True):
        """
        Plots data (and fitted line, if any) in Bode plots
        Return: fig
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
        Plots data (and fitted line, if any) in Nyquist plot
        Return: fig
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
        - filename: save name of file(s)
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
        Save data, circuit model, and plots to file
        - filename: save name of file(s)
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
        - filename: save name of file(s)
        """
        try:
            self.bode_plot.write_html(f'{folder}/{filename}_Bode.html')
            self.nyquist_plot.write_html(f'{folder}/{filename}_Nyquist.html')
        except AttributeError:
            print('Unable to save plots!')
        return

# %%
