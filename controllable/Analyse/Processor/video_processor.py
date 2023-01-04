# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/01/04 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import math
import matplotlib.pylab as plt
import numpy as np
import os
import pandas as pd
import sys
import time

# Third party imports

# Local application imports
print(f"Import: OK <{__name__}>")
np.set_printoptions(threshold=sys.maxsize)
 
class VideoProcessor(object):
    """
    Enables processing large amounts of video files with few lines of code

    Args:
        root_dir (str): directory that contains al folders with 'yyyy-MM-dd_HHmm' convention (i.e. session folders)
    """
    def __init__(self, root_dir):
        self._root = root_dir
        self._session = ''
        self._name_suffix = ''
        self.metrics_titles = []
        self.start_time = time.time()
        self.y_axes = [
            {'label': 'Length (x)', 'column': 'length_x'},
            {'label': 'Voltage', 'column': 'voltage_avg'}
        ]
        
        self.active_folder = ''
        self.background = None
        self.calculator = None
        self.datalog_df = pd.DataFrame()
        self.frame_ROI_shape = (0,0)    #h,w
        self.track_ROI_shape = (0,0)    #h,w
        
        self.suffix_frame_ROI = ''
        self.suffix_track_ROI = ''
        pass
    
    @property
    def session(self):
        return f'{self.root}/{self._session}'
    
    @session.setter
    def session(self, new_session):
        if os.path.exists(f'{self.root}/{new_session}'):
            self._session = new_session
        else:
            print('Input a valid session directory / path.')
        return
    
    @property
    def root(self):
        return self._root
    
    @root.setter
    def root(self, new_root):
        if os.path.exists(new_root):
            self._root = new_root
        else:
            print('Input a valid root directory / path.')
        return
    
    def _build_file_directory(self, filename):
        """
        Generate complete filepath from filename

        Args:
            filename (str): name of file

        Returns:
            str: full filepath of file
        """
        return f'{self.session}/{self.active_folder}/{filename}'
    
    def calculateMetrics(self, frame, **kwargs):
        """
        Calculates the metrics from the frame

        Args:
            frame (numpy.array): array of pixel intensities for the filtered frame

        Returns:
            tuple: output values from metrics calculator
        """
        trkROI_shape = self.track_ROI_shape
        return self.calculator(frame=frame, trkROI_shape=trkROI_shape, **kwargs)

    def clearCache(self, clear_background=False, clear_calculator=False):
        """
        Clears the cache in preparation for the next round of processing

        Args:
            clear_background (bool, optional): whether to clear the background frame. Defaults to False.
            clear_metrics (bool, optional): whether to clear the metrics calculator. Defaults to False.
        """
        self.active_folder = ''
        if clear_background:
            self.background = None
        if clear_calculator:
            self.calculator = None
            self.clear_metrics = []
            self._name_suffix = ''
        self.datalog_df = pd.DataFrame()
        self.frame_ROI_shape = (0,0)    #h,w
        self.track_ROI_shape = (0,0)    #h,w
        
        self.suffix_frame_ROI = ''
        self.suffix_track_ROI = ''
        return

    def filterFrame(self, filename):
        """
        Filters the frame, by reading the .raw file and applying the mask from the .bin file

        Args:
            filename (str): filename of .raw file

        Returns:
            tuple: (bool) whether target was tracked, (numpy.array) array of pixel intensities for the masked frame
        """
        camROI = self.frame_ROI_shape
        trkROI = self.track_ROI_shape
        frame_number= int(filename.replace('.raw','')[5:])
        feed_filename = self._build_file_directory(filename)
        mask_filename = self._build_file_directory(f'mask{frame_number-1}_{self.suffix_track_ROI}.bin')
        # print(f'{feed_filename}, {mask_filename}')
        
        x_center, y_center = self.datalog_df.loc[frame_number, ['displacement_x', 'displacement_y']]
        v_bounds = (int(y_center-trkROI[0]/2), int(y_center+trkROI[0]/2))
        h_bounds = (int(x_center-trkROI[1]/2), int(x_center+trkROI[1]/2))
        
        feed_matrix = np.fromfile(feed_filename, dtype=np.int16, sep="")
        feed_matrix = feed_matrix.reshape(camROI)
        frame_wo_bg = np.maximum(feed_matrix-self.background, np.zeros(camROI))
        
        mask_matrix = np.fromfile(mask_filename, dtype=np.int8, sep="")
        mask_px_num = len(mask_matrix)
        extension = trkROI[0]*trkROI[1]-mask_px_num
        if extension:
            new_shape = [*trkROI]
            padding = [[0,0],[0,0]]
            if mask_px_num % trkROI[0] == 0:
                new_shape[1] = int(mask_px_num/trkROI[0])
                padding[1][int(x_center/camROI[1])] = int(trkROI[1] - new_shape[1])
            elif mask_px_num % trkROI[1] == 0:
                new_shape[0] = int(mask_px_num/trkROI[1])
                padding[0][int(y_center/camROI[0])] = int(trkROI[0] - new_shape[0])
            partial_mask_matrix = mask_matrix.reshape(tuple(new_shape))
            mask_matrix = np.pad(partial_mask_matrix, padding)
            # print(filename)
            # print(tuple(new_shape))
        else:
            mask_matrix = mask_matrix.reshape(trkROI)
        
        padding = [
            (abs(min(0, v_bounds[0])), max(0, v_bounds[1] - camROI[0])),
            (abs(min(0, h_bounds[0])), max(0, h_bounds[1] - camROI[1])),
        ]
        frame_wo_bg = np.pad(frame_wo_bg, padding, mode='constant')
        track_wo_bg = frame_wo_bg[v_bounds[0]:v_bounds[1], h_bounds[0]:h_bounds[1]]
        if mask_matrix.sum() == 0:
            return False, track_wo_bg
        track_masked = np.multiply(track_wo_bg, mask_matrix)
        return True, track_masked.reshape(trkROI)
    
    def getBackground(self):
        """
        Gets the background frame for the session

        Returns:
            numpy.array: array of pixel intensities for the background frame
        """
        self.getDimensions()
        background = np.fromfile(f'{self.session}/Background.raw', dtype=np.int16, sep="")
        self.background = background.reshape(self.frame_ROI_shape)
        return self.background
    
    def getDatalog(self):
        """
        Reads the datalog from .txt file

        Returns:
            bool: whether getting the datalog file is a success
        """
        headers = [
            'frame_num',
            'frame_time',
            'displacement_y',
            'displacement_x',
            'voltage_1',
            'voltage_2',
            'length_y',
            'length_x',
            'intensity_total'
        ]
        datalog_path = self._build_file_directory('datalog.txt')
        if not os.path.exists(datalog_path):
            return False
        datalog = np.loadtxt(self._build_file_directory('datalog.txt'))
        datalog_df = pd.DataFrame(datalog, columns=headers)
        self.datalog_df = datalog_df.astype({'frame_num':int})
        self.datalog_df['frame_num'] += 1
        self.datalog_df.set_index('frame_num', inplace=True)
        self.datalog_df = self.datalog_df[self.datalog_df['frame_time']!=0]
        self.datalog_df.dropna(inplace=True)
        
        self.datalog_df['time_ms'] = np.cumsum(self.datalog_df['frame_time'])
        self.datalog_df['time_s'] = self.datalog_df['time_ms']/1000
        self.datalog_df['voltage_avg'] = np.mean(self.datalog_df[['voltage_1', 'voltage_2']], axis=1)
        self.datalog_df['voltage_diff'] = np.concatenate([np.array([0]), np.diff(self.datalog_df['voltage_avg'])])
        self.datalog_df['instance_on'] = (self.datalog_df['voltage_diff']>9)
        self.datalog_df['instance_off'] = (self.datalog_df['voltage_diff']<-9)
        return True
        
    def getDimensions(self):
        """
        Gets the camera ROI and track ROI shapes
        """
        height_width = self.active_folder.split('_')[-2:]
        self.frame_ROI_shape = (int(height_width[0][1:]), int(height_width[1][1:]))
        self.suffix_frame_ROI = f'{height_width[0]}_{height_width[1]}'
        
        for filename in os.listdir(self._build_file_directory('')):
            if filename.endswith('.bin'):
                filename = filename.replace('.bin', '')
                height_width = filename.split('_')[-2:]
                self.track_ROI_shape = (int(height_width[0][1:]), int(height_width[1][1:]))
                self.suffix_track_ROI = f'{height_width[0]}_{height_width[1]}'
                break
        return
    
    def loadCalculator(self, func, metrics_titles):
        """
        Load a metrics calculator function and the names of the metrics calculated
        
        Args:
            func (function): a function that takes 'frame' as the first argument, as well as other keyword arguments
            metrics_titles (list): list of metric names
        """
        self.calculator = func
        self.metrics_titles = metrics_titles
        return
    
    def plot(self, shift=False, save=False, show=True):
        """
        Plots the metrics for the video
        
        Args:
            shift (bool): whether to shift the plot to the first 'voltage-on' instance
            save (bool): whether to save plot figure
            show (bool): whether to show tbe resulting plot inline
        """
        first_on_index = self.datalog_df.index[0]
        if shift:
            first_on_index = min(self.datalog_df[self.datalog_df['instance_on']].index)
        plot_df = self.datalog_df.loc[first_on_index:,:].copy()
        plot_df['time_ms'] -= plot_df.at[first_on_index, 'time_ms']
        plot_df['time_s'] -= plot_df.at[first_on_index, 'time_s']
        
        fig, ax = plt.subplots()
        plot_df.plot(x='time_s', y=self.y_axes[0]['column'], ax=ax, label=self.y_axes[0]['label'])
        plt.ylim(bottom=0)
        plot_df.plot(x='time_s', y=self.y_axes[1]['column'], ax=ax, secondary_y=True, label=self.y_axes[1]['label'])
        plt.xlabel('Time(s)')
        video_name = self.active_folder.split('_')[0]
        title = f"{self._session} {video_name}"
        plt.title(title)
        if save:
            plt.savefig(f"{self.session}/plot_{video_name}_{self._name_suffix}.svg", format='svg')
        if show:
            plt.show()
        return
    
    def process(self, folder, save_csv=False):
        """
        Process the raw images/frames in the video folder and calculate metrics

        Args:
            folder (str): folder name of video
            save_csv (bool, optional): whether to save datalog to CSV. Defaults to False.

        Returns:
            bool: whether processing is a success
        """
        start_time = time.time()
        self.clearCache()
        self.active_folder = folder
        if not self.getDatalog():
            return False
        self.getDimensions()
        if type(self.background) == type(None):
            self.getBackground()
        print(f"Processing {self._build_file_directory('')}...")
        
        index = []
        metrics_list = []
        for filename in os.listdir(self._build_file_directory('')):
            if not filename.endswith('.raw'):
                continue
            frame_number= int(filename.replace('.raw','')[5:])
            if frame_number not in self.datalog_df.index:
                continue
            ret, frame = self.filterFrame(filename)
            metrics = self.calculateMetrics(frame)
            metrics_list.append(metrics)
            index.append(frame_number)
        metrics_df = pd.DataFrame(metrics_list, columns=self.metrics_titles)
        metrics_df['frame_num'] = index
        metrics_df.set_index('frame_num', inplace=True)
        self.datalog_df = self.datalog_df.join(metrics_df,rsuffix='_metric')
        if save_csv:
            self.saveCSV()
        
        elapsed_time = time.time() - start_time
        print(f'Elapsed time: {round(elapsed_time,3)}s')
        return True
    
    def processAll(self, plot=False, shift=False, save=False, show=True):
        """
        Process all the video folders in the same session
        
        Args:
            plot (bool, optional): whether to generate plot figures. Defaults to False.
            shift (bool, optional): whether to shift the plot to the first 'voltage-on' instance. Defaults to False.
            save (bool, optional): whether to save plot figures and datalog. Defaults to False.
            show (bool, optional): whether to show tbe resulting plots inline. Defaults to True.
        """
        start_time = time.time()
        self.clearCache(clear_background=True)
        for folder in os.listdir(self.session):
            if not folder.startswith('Video') or '.' in folder:
                continue
            processed = self.process(folder)
            if not processed:
                continue
            if plot:
                self.plot(shift, save, show)
            # break
        batch_time = time.time() - start_time
        minutes, seconds = divmod(batch_time, 60)
        print(f'Batch time: {int(minutes)}min {round(seconds,3)}s')
        return
    
    def saveCSV(self):
        """
        Save datalog and calculated values into CSV file

        Returns:
            pd.Dataframe: Datalog dataframe
        """
        video_name = self.active_folder.split('_')[0]
        self.datalog_df.to_csv(f"{self.session}/{video_name}_{self._name_suffix}.csv")
        return self.datalog_df
    
    def setNameSuffix(self, name_suffix):
        """
        Set suffix for filenames to save under

        Args:
            name_suffix (str): Filename suffix
        """
        self._name_suffix = name_suffix
        return
    
    def setYAxes(self, y_axis_index, label_column_dict):
        """
        Set y axes to plot against 'Time(s)'

        Args:
            y_axis_index (int): index of interested y axis
            label_column_dict (dict): Dictionary of 'label' and 'column'
        """
        self.y_axes[y_axis_index] = label_column_dict
        return

# %%
