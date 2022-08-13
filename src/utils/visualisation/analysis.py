import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse.linalg import spsolve
import scipy.signal as signal

class Onset(object):
    """
    'Onset' class contains methods to find the baseline, slope, and intercept of plots that
    require the finding of an onset value, such as band-gaps and work functions.
    """
    def __init__(self):
        self.data = pd.DataFrame()
        return


    def find_baseline(self, y, asc=True, proportion=3):
        '''
        Finds the baseline of the plot
        - y: y-value column name
        - asc: whether the data is sorted in an ascending order
        - proportion: reciprocal of the fraction of data points to use in finding the baseline

        Returns: baseline value (float)
        '''
        if asc:
            points = self.data.head(int(len(self.data)/proportion))[y]
        else:
            points = self.data.tail(int(len(self.data)/proportion))[y]
        self.baseline = points.mean()
        self.data['baseline'] = self.baseline
        return self.baseline


    def find_slope(self, x, y, asc=True, proportion=3):
        '''
        Finds the slope of the plot (y = mx + c)
        - x: x-value column name
        - y: y-value column name
        - asc: whether the data is sorted in an ascending order
        - proportion: reciprocal of the fraction of data points to use in finding the slope

        Returns: (m, c)
        '''
        if asc:
            points = self.data.tail(int(len(self.data)/proportion))[[x, y]]
        else:
            points = self.data.head(int(len(self.data)/proportion))[[x, y]]
        x_data = points[x]
        y_data = points[y]
        self.model = np.polyfit(x_data, y_data, 1)
        self.data['slope'] = self.data[x]*self.model[0] + self.model[1]
        self.data['overall'] = self.data[['slope', 'baseline']].max(axis=1)
        return self.model


    def find_intercept(self, x, y, asc=True, ratio_base=3, ratio_slope=3):
        '''
        Finds the onset value (or the intercept of baseline and slope)
        - x: x-value column name
        - y: y-value column name
        - asc: whether the data is sorted in an ascending order
        - ratio_base: reciprocal of the fraction of data points to use in finding the baseline
        - ratio_slope: reciprocal of the fraction of data points to use in finding the slope

        Returns: intercept coordinates (float, float)
        '''
        self.find_baseline(y, asc, ratio_base)
        self.find_slope(x, y, asc, ratio_slope)
        self.intercept = ((self.baseline - self.model[1]) / self.model[0], self.baseline)
        return self.intercept


class Peaks(object):
    """
    'Peaks' class contains methods to correct for the baseline spectrum and locate the peaks of
    the signal and their prominences, such as in FTIR spectroscopy. 
    """
    def __init__(self):
        self.name = ''
        self.data = pd.DataFrame()
        self.bdf = pd.DataFrame()
        self.pdf = pd.DataFrame()
        return


    def baseline_als(self, y, lam, p, niter=10):
        '''
        Derive the baseline for plot
        - y: y values
        - lam: smoothness parameter
        - p: smoothening rate
        - niter: number of iterations

        Returns: corrected baseline vector (np.array)
        '''
        L = len(y)
        D = sparse.diags([1,-2,1],[0,-1,-2], shape=(L,L-2))
        D = lam * D.dot(D.transpose()) # Precompute this term since it does not depend on `w`
        w = np.ones(L)
        W = sparse.spdiags(w, 0, L, L)
        for i in range(niter):
            W.setdiag(w) # Do not create a new matrix, just update diagonal values
            Z = W + D
            z = spsolve(Z, w*y)
            w = p * (y > z) + (1-p) * (y < z)
        return z


    def baseline_correction(self, y, wavenumber_range, lam=2E5, p=0.95, niter=1000):
        '''
        Correct for plot baseline
        - y: y-value column name
        - wavenumber_range: x range of interest
        - lam: smoothness parameter
        - p: smoothening rate
        - niter: number of iterations

        Returns: dataframe of corrected baseline (pd.Dataframe)
        '''
        y_data = self.bdf[y]
        base = self.baseline_als(y=y_data, lam=lam, p=p, niter=niter)
        self.bdf['baseline'] = base
        self.bdf['corrected'] = y_data - base

        self.bdf = self.bdf[(self.bdf['wavenumber']>=wavenumber_range[0]) & (self.bdf['wavenumber']<=wavenumber_range[1])].copy()
        self.bdf['sample'] = self.name
        return self.bdf


    def locate_peaks(self, peak_cutoff=0.0012):
        '''
        Locates the peaks and their prominences
        - peak_cutoff: threshold to determine if peaks are prominent enough from their background

        Returns: dataframe of the peaks and prominences (pd.Dataframe)
        '''
        y = self.bdf['corrected']*-1
        peak_ids = signal.argrelextrema(y.to_numpy(), np.greater, order=3)[0]
        prominences= signal.peak_prominences(y, peak_ids)[0]
        self.peak_ids = [peak_ids[i] for i in range(len(prominences)) if prominences[i]>peak_cutoff]
        self.prominences = [p for p in prominences if p>peak_cutoff]

        self.pdf = self.bdf.iloc[self.peak_ids,:].copy()
        self.pdf['prominence'] = self.prominences
        self.pdf['sample'] = self.name + ' peak'

        return self.pdf

