# %%
# -*- coding: utf-8 -*-
"""
Created on Fri 2022/06/18 09:00:00

@author: Chang Jie

Impedance package documentation can be found at:
https://impedancepy.readthedocs.io/en/latest/index.html
"""
import os, sys
import clr
import json
import pandas as pd
import plotly.express as px

from eis_datatype import ImpedanceSpectrum

# Depend on computer setup and installation
THERE = {'misc': 'utils\\misc'}
here = os.getcwd()
base = here.split('src')[0] + 'src\\'
there = {k: base+v for k,v in THERE.items()}
for v in there.values():
    sys.path.append(v)
SENSORPAL_INSTALLATION = r"C:\Users\leongcj\Desktop\Analog Devices\SensorPal" if 'leongcj' in here else r"C:\Program Files (x86)\Analog Devices\SensorPal"
sys.path.append(SENSORPAL_INSTALLATION)
clr.AddReference('SensorPal.API')

from miscfunctions import display_ports
from SensorPal.API import API as SensorPalAPI

COM_PORT = display_ports()
sensorpal = SensorPalAPI()

print(f"Import: OK <{__name__}>")

# %%
class Sensorpal(object):
    """
    Sensorpal object that controls electrical characterization of sample.
    - filename: name of json file to load settings
    """
    def __init__(self, filename='', address=COM_PORT):
        try:
            with open(filename) as json_file:
                self.config = json.load(json_file)
        except Exception as e:
            print(e)
            print(f"Unable to load json file: {filename}")
            return
        
        self.technique = self.config["technique"]
        self.technique_parameters = None
        self.isConnected = False
        self.data = pd.DataFrame(columns=self.config["data columns"])
        
        self.connect(address)
        return

    def configure(self, settings={}):
        """
        Configure measurement parameters
        - settings: dictionary of parameter name, value pairs to be set
        """
        if not self.isConnected:
            return
        if type(settings) == dict and len(settings):
            for key, value in settings.items():
                sensorpal.UpdateTechniqueParameter(self.technique, self.technique_parameters, key, value)
        else:
            for parameter in self.config['parameters']:
                print(f"Set: {parameter['name']}")
                sensorpal.UpdateTechniqueParameter(self.technique, self.technique_parameters, parameter['name'], parameter['value'])
        return

    def connect(self, address):
        """
        Establish connection with hardware
        """
        try:
            sensorpal.OpenConnection(address)
            self.technique_parameters = sensorpal.GetDefaultTechniqueParameters(self.technique)
            self.isConnected = True
            self.configure()
        except Exception as e:
            print(e)
            print(f"Unable to open '{address}'. Is it connected?")
            self.isConnected = False
            raise(e)
        return

    def measure(self):
        """
        Start measurement
        """
        if not self.isConnected:
            return
        
        sensorpal.Measure(self.technique, self.technique_parameters)
        while sensorpal.IsMeasuring():
            graph_data = sensorpal.GetGraphData(self.config['plot']['plot_type'])
            if graph_data:
                print("=" * 50)
                for field_index in range(0, len(graph_data.InfoPaneNames)):
                    if graph_data.InfoPaneNames[field_index]:
                        print("%20s : %s" % (
                            graph_data.InfoPaneNames[field_index],
                            graph_data.InfoPaneValues[field_index]))
                self.data.loc[len(self.data.index)] = [graph_data.InfoPaneValues[3], graph_data.InfoPaneValues[1], graph_data.InfoPaneValues[2]]
        
        self.data = self.data.astype('float')
        sensorpal.CloseConnection()
        self.isConnected = False
        return self.data

    def plot(self, use_plotly=True):
        """
        Plot output
        - use_plotly: whether to use Plotly plotting library
        """
        x_axis, y_axis = self.config['plot']['x_axis'], self.config['plot']['y_axis']
        if use_plotly:
            fig = px.scatter(self.data, x_axis, y_axis)
            fig.show()
        else:
            # fig = plt.scatter(self.data[x_axis], self.data[y_axis])
            # if show_plot:
            #     plt.show()
            pass
        return [fig]


class SensorEIS(Sensorpal):
    """
    Sensorpal object that controls EIS characterization of sample.
    - filename: name of json file to load settings for EIS measurment
    """
    def __init__(self, filename='Measurement_Battery Impedance.json', address=COM_PORT):
        super().__init__(filename, address)
        self.spectra = {}
        self.sample_num = 0

    def measure(self):
        """
        Initiate EIS measurement.
        """
        data = super().measure()
        self.sample_num += 1
        print(f'Spectrum number: {self.sample_num}')
        self.spectra[self.sample_num] = ImpedanceSpectrum(data=data, name=f'Spectrum {self.sample_num}')
        return data

    def plot(self, sample_num=0, plot_type='nyquist'):
        """
        Plot the data.
        - sample_num: id of sample data to plot, if 0, plots all data,  if -1, latest data
        """
        figs = []
        if sample_num == 0:
            for i in range(self.sample_num):
                spectrum = self.spectra[i+1]
                fig = spectrum.plot(plot_type)
                figs.append(fig)
        elif sample_num > 0:
            spectrum = self.spectra[sample_num]
            fig = spectrum.plot(plot_type)
            figs.append(fig)
        elif sample_num == -1:
            sample_num = len(self.spectra)
            spectrum = self.spectra[sample_num]
            fig = spectrum.plot(plot_type)
            figs.append(fig)
        return figs

    def save(self, sample_num=0):
        """
        Saves the EIS data
        - sample_num: id of sample data to save, if 0, saves all data, if -1, latest data
        """
        if sample_num == 0:
            for i in range(self.sample_num):
                self.spectra[i+1].saveData()
        elif sample_num > 0:
            self.spectra[sample_num].saveData()
        elif sample_num == -1:
            sample_num = len(self.spectra)
            self.spectra[sample_num].saveData()
        return

    def setName(self, sample_num=-1, name=''):
        """
        Name the sample data.
        - name: name of sample
        - sample_num: id of sample data, if -1, latest data
        """
        if len(name) == 0:
            print('Enter a name!')
            return
        if sample_num == -1:
            sample_num = len(self.spectra)
            self.spectra[sample_num].name = name
        if sample_num > 0:
            self.spectra[sample_num].name = name
        else:
            print('Enter a valid sample number!')
        return


if __name__ == "__main__":
    eis = SensorEIS()
    eis.measure()
    eis.plot(-1)
    pass

# %%
