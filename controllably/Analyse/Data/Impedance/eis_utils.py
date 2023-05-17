# %% -*- coding: utf-8 -*-
"""
This module holds utility functions for EIS analysis.

Functions:
    analyse
    generate_guess
    nudge_points
    trim
"""
# Standard library imports
from __future__ import annotations
import cmath
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

# Third party imports
from impedance.models.circuits.fitting import extract_circuit_elements

# Local application imports
from ..toolbox import intersection, perpendicular_bisector
print(f"Import: OK <{__name__}>")

def analyse(data:pd.DataFrame, order:int = 4) -> tuple:
    """
    Analyse the Nyquist plot to get several features of the curve

    Args:
        order (int, optional): how many surrounding points to consider to determine local extrema. Defaults to 4.

    Returns:
        tuple: collection of curve features (frequency, nudged x values, nudeged y values, index of min points, index of max points, estimated r0, Warburg slope gradient, Warburg slope intercept)
    """
    data = data.copy()
    data.sort_values(by='Frequency', ascending=False, inplace=True)
    f = data['Frequency'].to_numpy()
    x = data['Real'].to_numpy()
    y = data['Imaginary'].to_numpy() * (-1)
    # Nudge running points to avoid curve from looping on itself
    x,y = nudge_points(x,y)

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

    # Get index of minima
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

    # Get index of maxima
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
        # Find centre of semicircle
        top_idx = max_idx[0]
        bot_idx = min_idx[1]
        mid_idx = int((top_idx+bot_idx)/2)
        line1 = perpendicular_bisector((x[top_idx], y[top_idx]), (x[mid_idx], y[mid_idx]))
        line2 = perpendicular_bisector((x[bot_idx], y[bot_idx]), (x[mid_idx], y[mid_idx]))
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

    # Fitting the ~45 degree slope tail
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

def generate_guess(
    circuit_string: str, 
    f: np.ndarray, 
    x: np.ndarray, 
    y: np.ndarray, 
    min_idx: list, 
    max_idx: list, 
    r0: float, 
    a: float, 
    b: float, 
    constants: dict = {}
) -> tuple[list, dict]:
    """
    Generate initial guesses from circuit string

    Args:
        circuit_string (str): string representation of circuit model
        f (np.ndarray): array of frequency values
        x (np.ndarray): array of x values
        y (np.ndarray): array of y values
        min_idx (list): list of indices of minimum points
        max_idx (list): list of indices of maximum points
        r0 (float): estimated value of r0
        a (float): intercept of Warburg slope
        b (float): gradient of Warburg slope
        constants (dict, optional): components to have fixed values. Defaults to {}.

    Returns:
        tuple[list, dict]: list of initial guesses; dictionary of constants to be set
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

def nudge_points(x_values:np.ndarray, y_values:np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Nudge points to avoid curve from looping on itself

    Args:
        x_values (np.ndarray): x values
        y_values (np.ndarray): y values

    Returns:
        tuple[np.ndarray, np.ndarray]: nudged x values; nudged y values
    """
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
    return x_values, y_values

def trim(f:np.ndarray, Z:np.ndarray, x:int, p:float = 0.15) -> tuple[np.ndarray, np.ndarray]:
    """
    Trim the 45-degree Warburg slope to avoid overfit

    Args:
        f (np.ndarray): array of frequencies
        Z (np.ndarray): array of complex impedances
        x (int): index of last minimum point (i.e. start / bottom of Warburg slope)
        p (float, optional): proportion of data points to trim out. Defaults to 0.15.

    Returns:
        tuple[np.ndarray, np.ndarray]: array of frequencies; array of complex impedances
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
