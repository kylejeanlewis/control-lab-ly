# %%
# -*- coding: utf-8 -*-
"""
Created on Fri 2022/06/18 09:00:00

@author: Chang Jie
"""
import os, sys
import pandas as pd

THERE = {'electrical': 'utils\\characterisation\\electrical'}
here = os.getcwd()
base = here.split('src')[0] + 'src'
there = {k: '\\'.join([base,v]) for k,v in THERE.items()}
for v in there.values():
    sys.path.append(v)

from eis_datatype import ImpedanceSpectrum
print(f"Import: OK <{__name__}>")

SAMPLE = 'A6'
FILE_EXT = '.txt'
MAIN_DIR = r'C:\Users\leongcj\Desktop\EIS Data'
# SAMPLE = 'EIS'
# FILE_EXT = '.csv'
# MAIN_DIR = r'C:\Users\leongcj\Desktop\Astar_git\polylectric\characterization\conductivity'
SRC_DIR = MAIN_DIR + f'\\{SAMPLE}'

class EISProcessor(object):
    def __init__(self):
        self.paths_of_interest = {}
        self.collection = {}
        self.src_dir = ''
        return

    def findFiles(self, src_dir, file_ext, load_memory=False):
        self.src_dir = src_dir
        self.paths_of_interest = {}
        for dir in os.listdir(src_dir):
            if file_ext in dir:
                name = dir.replace(file_ext, '')
                self.paths_of_interest[name] = os.path.join(src_dir, dir)
        if load_memory:
            for name, path in self.paths_of_interest.items():
                data = self.parseFile(path)
                self.collection[name] = ImpedanceSpectrum(name=name, data=data)
        return self.paths_of_interest

    def fitFile(self, name, save=True, folder='', global_opt=False, component_guesses={}, load_memory=False):
        try:
            spectrum = self.collection[name]
        except:
            spectrum = self.getSpectrum(name)
        spectrum.fit(global_opt=global_opt, component_guesses=component_guesses)
        spectrum.plotNyquist(show_plot=False)
        spectrum.plotBode(show_plot=False)
        if save:
            self.saveFile(spectrum, folder)
        if load_memory:
            self.collection[name] = spectrum
        return spectrum

    def fitFiles(self, names=[], save=True, folder='', global_opt=False, component_guesses={}, load_memory=False):
        if type(names) == str:
            name = names
            self.fitFile(name, save, folder, global_opt, component_guesses, load_memory)
        elif type(names) == list:
            if len(names) == 0:
                names = [n for n in self.paths_of_interest.keys()]
            for name in names:
                self.fitFile(name, save, folder, global_opt, component_guesses, load_memory)
        return

    def getSpectrum(self, name):
        path = self.paths_of_interest[name]
        data = self.parseFile(path)
        spectrum = ImpedanceSpectrum(name=name, data=data)
        return spectrum
    
    def parseFile(self, path):
        data = pd.read_csv(path, names=['Frequency', 'Real', 'Imaginary'], header=None)
        return data

    def saveFile(self, spectrum, folder=''):
        if len(folder) == 0:
            folder = f'{self.src_dir}/fitted'
        name = spectrum.name
        spectrum.saveData(filename=name, folder=f'{folder}/{name}')
        return spectrum

    def saveFiles(self, names=[], folder=''):
        if type(names) == str:
            name = names
            spectrum = self.collection[name]
            self.saveFile(spectrum, folder)
        elif type(names) == list:
            if len(names) == 0:
                names = [n for n in self.paths_of_interest.keys()]
            for name in names:
                spectrum = self.collection[name]
                self.saveFile(spectrum, folder)
        return

class AutoLabProcessor(EISProcessor):
    def __init__(self):
        super().__init__()
        return

    def parseFile(self, path):
        cols = ['Frequency', 'Real', '-Imaginary', 'Magnitude', '-Phase (deg)']
        data = pd.read_csv(path, names=cols, sep='\t', lineterminator='\n', header=1)
        data['Imaginary'] = data['-Imaginary'] * (-1)
        data = data[['Frequency', 'Real', 'Imaginary']].copy()
        return data

# %%
if __name__ == "__main__":
    processor = AutoLabProcessor()
    processor.findFiles(SRC_DIR, FILE_EXT)
    processor.fitFiles(
        names=[], 
        global_opt=False,
        load_memory=True
    )

# %%
if __name__ == "__main__":
    for spectrum in processor.collection.values():
        if spectrum.name:
            spectrum.plotNyquist()
            spectrum.getCircuitDiagram()
    

# %%
