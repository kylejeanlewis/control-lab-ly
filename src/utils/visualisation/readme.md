# Data Visualisation
This package generates the data visualisations for the different characterisation of samples, including:
1. FET \(Field Effect Transistor\) measurement
2. FTIR \(Fourier-Transform Infrared\) spectroscopy
3. HSI \(Hyperspectral Imaging\)
4. PESA \(Photoelectron Spectroscopy in Air\)
5. Spin speed calibration \(from surface profiler thickness measurements\)

# Dependencies
- os
- numpy, scipy, pandas
- plotly

# Modules
- \(main\) main
- \(helper\) analysis, filesearch, plotters
- \(characterisation\) calibration, FET, FTIR, HSI, PESA

## analysis
- _class_ **Onset** \(\)

    'Onset' class contains methods to find the baseline, slope, and intercept of plots that require the finding of an onset value, such as band-gaps and work functions.

    - _method_ **find_baseline** \(y, asc=True, proportion=3\)   

        Finds the baseline of the plot   
        \- y: y-value column name   
        \- asc: whether the data is sorted in an ascending order   
        \- proportion: reciprocal of the fraction of data points to use in finding the baseline

        Returns: baseline value \(float\)

    - _method_ **find_slope** \(x, y, asc=True, proportion=3\)

        Finds the slope of the plot \(y = mx + c\)   
        \- x: x-value column name   
        \- y: y-value column name   
        \- asc: whether the data is sorted in an ascending order   
        \- proportion: reciprocal of the fraction of data points to use in finding the slope

        Returns: \(m, c\)

    - _method_ **find_intercept** \(x, y, asc=True, ratio_base=3, ratio_slope=3\)   

        Finds the onset value \(or the intercept of baseline and slope\)   
        \- x: x-value column name   
        \- y: y-value column name   
        \- asc: whether the data is sorted in an ascending order   
        \- ratio_base: reciprocal of the fraction of data points to use in finding the baseline   
        \- ratio_slope: reciprocal of the fraction of data points to use in finding the slope   

        Returns: intercept coordinates \(float, float\)

- _class_ **Peaks** \(\)

    'Peaks' class contains methods to correct for the baseline spectrum and locate the peaks of the signal and their prominences, such as in FTIR spectroscopy. 

    - _method_ **baseline_als** \(y, lam, p, niter=10\)

        Derive the baseline for plot   
        \- y: y values   
        \- lam: smoothness parameter   
        \- p: smoothening rate   
        \- niter: number of iterations

        Returns: corrected baseline vector \(np.array\)

    - _method_ **baseline_correction** \(y, wavenumber_range, lam=2E5, p=0.95, niter=1000\)

        Correct for plot baseline   
        \- y: y-value column name   
        \- wavenumber_range: x range of interest   
        \- lam: smoothness parameter   
        \- p: smoothening rate   
        \- niter: number of iterations

        Returns: dataframe of corrected baseline \(pd.Dataframe\)

    - _method_ **locate_peaks** \(peak_cutoff=0.0012\)

        Locates the peaks and their prominences   
        \- peak_cutoff: threshold to determine if peaks are prominent enough from their background

        Returns: dataframe of the peaks and prominences \(pd.Dataframe\)

## calibration
- _function_ **extract_data** \(all_paths, db_dir, update_db=True\)

    Extracts data from raw text files retreived from surface profiler   
    \- all_paths: dictionary of all the filepaths   
    \- db_dir: database filepath   
    \- update_db: whether or not to write new entries into the database

    Returns: dataframe of Sample ID and Thickness \(pd.Dataframe\)

- _function_ **process** \(all_paths, measurement_object, sample_ids, desired_thickness, logs_path, force_fit=False\)

    Main function to process the data and generate the visualisation   
    \- all_paths: dictionary of all the filepaths   
    \- measurement_object: the class used to handle the data   
    \- sample_ids: ids of interested samples   
    \- desired_thickness: target thickness of film in nm   
    \- logs_path: path of folder containing the database   
    \- force_fit: whether to force fit the curve to y = a*\(x**-0.5\)

    Returns: measurement_object \(SpeedCollection\)

- _class_ **SpeedCollection** \(data\)

    'SpeedCollection' class contains methods to fit the curve from the data points, plot the curve, and recommend the appropriate spin speed for desired thickness.   
    \- data: thickness data

    - _method_ **fit_power_curve** \(force_fit=False\)

        Fits the curve using the relation y = a*\(x**b\)   
        \- force_fit: whether to force b = -0.5

        Returns: \(\(b, a\), x_values, y_values\)

    - _method_ **plot** \(show_recommended=False, show_outlier=False, show_plot=False\)

        Generates the plot   
        \- show_recommended: whether to plot the recommended spin speed   
        \- show_outlier: whether to plot the outlier measurement values   
        \- show_plot: whether to display the plot

        Returns: plot figure \(plotly.graph_objects.figure\)

    - _method_ **recommend_spin_speed** \(desired_thickness=30, show_plot=False\)

        Recommends the appropriate spin speed for the target thickness   
        \- desired_thickness: target thickness in nm   
        \- show_plot: whether to display the plot

        Returns: optimal speed \(float\)

## filesearch
- _function_ **get_basedir** \(suffix=''\)

    Get the root directory of machine   
    \- suffix: deeper path where the data files and logs can be found \(i.e. Teams sync folder\)

    Returns: full path of base directory \(str\)

- _function_ **locate_path** \(main, sub, keyword, dir_type='file', file_ext=''\)

    Locate the paths of interest for a particular keyword and extension type   
    \- main: main directory or folder   
    \- sub: sub directory or folder   
    \- keyword: string to be found in path names \(i.e. sample IDs\)   
    \- dir_type: file or folder   
    \- file_ext: file extension

    Returns: {filename: full_path}

- _function_ **locate_paths** \(main, sub, keywords, dir_type='file', file_ext=''\)

    Locate the paths of interest for a few keywords and extension type   
    \- main: main directory or folder   
    \- sub: sub directory or folder   
    \- keywords: strings to be found in path names \(i.e. sample IDs\)   
    \- dir_type: file or folder   
    \- file_ext: file extension

    Returns: {keyword: {filename: full_path}}

## FET
- _function_ **read_data** \(save_details\)

    Read the processed data files   
	\- save_details: the details on the folder, subfolder, and format of the saved files

	Returns: {idvd_filnames: pd.Dataframe}, {idvg_filnames: pd.Dataframe}, \[labels\]

- _function_ **extract_data** \(save_details, param_list, interval=1, save_data=True\)

    Function for extracting data from result's csv files   
	\- save_details: the details on the folder, subfolder, and format of the saved files   
	\- param_list: list of voltage parameters / settings   
	\- interval: size of data reading window   
	\- save_data: whether to save the processed data

	Returns: {idvd_filnames: pd.Dataframe}, {idvg_filnames: pd.Dataframe}, \[labels\]

- _function_ **process** \((all_paths, measurement_object, params, interval=1, save_csv=False\)

    Main function to process the data and generate the visualisation   
    \- all_paths: dictionary of all the filepaths   
    \- measurement_object: the class used to handle the data   
    \- channel_lengths: channel_lengths for different devices     
	\- interval: size of data reading window   
    \- y_axis: the y-values to plot for respective graphs   
	\- save_csv: whether to save the processed data

    Returns: {sample_ids: FET_grid} or None

- _class_ **FET_grid** \(name, datasets, path, labels, volt_var, volt_const, x_axis, y_axis\)   

    'FET_grid' class contains methods to create a collection of FET_single objects, as well as to generate grid plots and individual plots for each device.
    \- name: name of sample
    \- datasets:
    \- path: directory to save to / read from
    \- labels: device number
    \- volt_var:
    \- volt_const:
    \- x_axis:
    \- y_axis:

    - _method_ **create_collection** \(\)

        Creates a collection of FET_single objects

		Returns: list of FET_single objects
        
    - _method_ **plot_grid** \(chip_size=\(4,2\)\)

        Generates a grid plot of devices on the chip   
		\- chip_size: dimensions of the layout of the devices

		Returns: plot figure \(plotly.graph_objects.figure\)

    - _method_ **plot_individual** \(save_plot=False, save_parse=False\)

        Generates a individual plots for devices on the chip   
		\- save_plot: whether to save the plots   
		\- save_parse: whether to save the parsed data from the operation

		Returns: None

- _class_ **FET_single** \(name, dataset, path, labels, volt_var, volt_const, x_axis, y_axis\)

    'FET_single' class contains methods to parse the data and plot them, as well as to perform multiple parse and plot operations.   
    \- name:   
    \- dataset:   
    \- path:   
    \- labels:   
    \- volt_var:   
    \- volt_const:   
    \- x_axis:   
    \- y_axis:   

    - _method_ **parse** \(df, title, save_parse=False\)

        Parse data from csv files to get a table that is suitable for plotting   
		\- df: dataframe read from csv file   
		\- title: filename for parsed data   
		\- save_parse: whether to save parsed data

		Returns: None

    - _method_ **parse_all** \(save_parse=False\)

        Parse data from multiple csv files to get tables that are suitable for plotting   
		\- save_parse: whether to save parsed data

		Returns: None

    - _method_ **plot** \(df, title, show_plot=False, save_plot=False, save_parse=False\)

        Plots data from csv files after being parsed   
		\- df: dataframe read from csv file   
		\- title: title of plot   
		\- show_plot: whether to display the plot   
		\- save_plot: whether to save the plot   
		\- save_parsed: whether to save parsed data

		Returns: plot figure \(plotly.graph_objects.figure\)

    - _method_ **plot_all** \(save_plot=False, save_parse=False\)

        Plots data from csv files after being parsed   
		\- save_plot: whether to save the plot   
		\- save_parsed: whether to save parsed data

		Returns: None

## FTIR
- _function_ **process** \(all_paths, measurement_object, home_path\)

    Main function to process the data and generate the visualisation   
    \- all_paths: dictionary of all the filepaths   
    \- measurement_object: the class used to handle the data   
    \- home_path: parent directory to which the overall plot can be saved

    Returns: dataframe of peaks and prominences \(pd.Dataframe\) or None

- _class_ **FTIR** \(name, path\)

    'FTIR' class is a child class of 'Peaks', and has an extra method of generating the plots.   
    \- name:   
    \- path:   

    - _method_ **plot** \(show_plot=True, save_plot=True\)

        Generates the plot   
        \- show_plot: whether to display the plot   
        \- save_plot: whether to save the plot

        Returns: plot figure \(plotly.graph_objects.figure\)

## HSI
- _function_ **process** \(\)

    Main function to process the data and generate the visualisation   
    \- all_paths: dictionary of all the filepaths   
    \- measurement_object: the class used to handle the data   
    \- sample_ids: ids of interested samples

    Returns: measurement object \(HSI\) or None

- _class_ **HSI** \(name, path, sample_ids\)

    'HSI' class is a child class of 'Onset', and has additional methods to get the absorbance values and to generate plots.   
    \- name:   
    \- path:   
    \- sample_ids:

    - _method_ **getAbsorbance** \(\)

        Calculates the absorbance values from the transmittance values in the output data

        Returns: dataframe of absorbance \(pd.Dataframe\)

    - _method_ **plot** \(show_plot=True, save_plot=True\)

        Generates an aggregated plot of all samples in the batch
        \- show_plot: whether to display the plot
        \- save_plot: whether to save the plot

        Returns: plot figure \(plotly.graph_objects.figure\)

- _class_ **HSI_sample** \(name, folder, adf\)

    'HSI' class is a child class of 'HSI', and has a modified 'plot' method.   
    \- name:   
    \- folder:   
    \- adf:

    - _method_ **plot** \(show_plot=True, save_plot=True\)

        Generates a plot of the data and the fitted lines and intercept
        \- show_plot: whether to display the plot
        \- save_plot: whether to save the plot

        Returns: plot figure \(plotly.graph_objects.figure\)

## PESA
- _function_ **process** \(all_paths, measurement_object\)

    Main function to process the data and generate the visualisation   
    \- all_paths: dictionary of all the filepaths   
    \- measurement_object: the class used to handle the data

    Returns: {sample_ids: PESA} or None

- _class_ **PESA** \(name, path\)

    'PESA' class is a child class of 'Onset', and has an extra method to generate plots.   
    \- name:   
    \- path:

    - _method_ **plot** \(show_plot=True, save_plot=True\)

        Generates a plot of the data and the fitted lines and intercept
        \- show_plot: whether to display the plot
        \- save_plot: whether to save the plot

        Returns: plot figure \(plotly.graph_objects.figure\)

## plotters
- _function_ **plot_add_point** \(fig, x_coord, y_coord, name, text, mode, text_position, show_plot=False, save_plot=False, save_details=None\)

    Adds point\(s\) to existing figure object   
    \- fig: figure object   
    \- x_coord: x-coordinate\(s\)   
    \- y_coord: y-coordinate\(s\)   
    \- name: name\(s\) of point\(s\) / legend   
    \- text: text label\(s\)   
    \- mode: type of plotting mode \(i.e. with or without text\)   
    \- text_position: position text label for point\(s\)   
    \- show_plot: whether to display the plot   
    \- save_plot: whether to save the plot   
    \- save_details: file saving details \(folder, subfolder, filename\)

    Returns: plot figure \(plotly.graph_objects.figure\)

- _function_ **plot_add_line** \(fig, x_data, y_data, name, show_plot=False, save_plot=False, save_details=None\)

    Adds a line to existing figure object   
    \- fig: figure object   
    \- x_data: x-coordinates   
    \- y_data: y-coordinates   
    \- name: name of line / legend   
    \- show_plot: whether to display the plot   
    \- save_plot: whether to save the plot   
    \- save_details: file saving details \(folder, subfolder, filename\)

    Returns: plot figure \(plotly.graph_objects.figure\)

- _function_ **plot_add_subplot** \(big_fig, fig, position, x_title, y_title\)

    Adds a single figure to existing grid   
    \- big_fig: grid plot object   
    \- fig: figure object   
    \- position: position in grid to add the figure   
    \- x_title: horizontal axis title   
    \- y_title: vertical axis title   

    Returns: plot figure \(plotly.graph_objects.figure\)

- _function_ **plot_blank_grid** \(dimension, main_title, subplot_titles, h_space=0.1, v_space=0.15\)

    Initialise / create new blank grid plot object   
    \- dimension: size of grid   
    \- main_title: overall title of grid plot   
    \- subplot_titles: titles of individual subplots   
    \- h_space: horizontal spacing between subplots   
    \- v_space: vertical spacing between subplots

    Returns: plot figure \(plotly.graph_objects.figure\)

- _function_ **plot_combined** \(figs, x_title, y_title, dimension, main_title, subplot_titles, h_space=0.1, v_space=0.15, show_plot=False, save_plot=False, save_details=None\)

    Generate a combined grid plot   
    \- figs: list of figures to be added to grid   
    \- x_title: horizontal axis title   
    \- y_title: vertical axis title   
    \- dimension: size of grid   
    \- main_title: overall title of grid plot   
    \- subplot_titles: titles of individual subplots   
    \- h_space: horizontal spacing between subplots   
    \- v_space: vertical spacing between subplots   
    \- show_plot: whether to display the plot   
    \- save_plot: whether to save the plot   
    \- save_details: file saving details \(folder, subfolder, filename\)

    Returns: plot figure \(plotly.graph_objects.figure\)

- _function_ **plot_kinked_fit_points** \(df, x, y, title, x_title, y_title, data_plot_type='scatter', show_plot=False, save_plot=False, save_details=None\)

    Plot data points with a fitted kinked line   
    \- df: dataframe   
    \- x: x-value column name   
    \- y: y-value column name   
    \- title: title of plot   
    \- x_title: horizontal axis title   
    \- y_title: vertical axis title   
    \- data_plot_type: scatter or line   
    \- show_plot: whether to display the plot   
    \- save_plot: whether to save the plot   
    \- save_details: file saving details \(folder, subfolder, filename\)

    Returns: plot figure \(plotly.graph_objects.figure\)

- _function_ **plot_line** \(df, x, y, title=None, x_title=None, y_title=None, names=None, line_width=None, show_plot=False, save_plot=False, save_details=None\)

    Plot data points in a line   
    \- df: dataframe   
    \- x: x-value column name   
    \- y: y-value column name   
    \- title: title of plot   
    \- x_title: horizontal axis title   
    \- y_title: vertical axis title   
    \- names: names of data points \(i.e. sample IDs\)   
    \- line_width: width of line plot   
    \- show_plot: whether to display the plot   
    \- save_plot: whether to save the plot   
    \- save_details: file saving details \(folder, subfolder, filename\)

    Returns: plot figure \(plotly.graph_objects.figure\)

- _function_ **plot_line_point** \(line_df, point_df, x, y, title, x_title, y_title, names=None, line_width=None, show_plot=False, save_plot=False, save_details=None\)

    Combine a line plot and a scatter plot   
    \- line_df: dataframe for line plot   
    \- point_df: dataframe for scatter plot   
    \- x: x-value column name   
    \- y: y-value column name   
    \- title: title of plot   
    \- x_title: horizontal axis title   
    \- y_title: vertical axis title   
    \- names: names of data points \(i.e. sample IDs\)   
    \- line_width: width of line plot   
    \- show_plot: whether to display the plot   
    \- save_plot: whether to save the plot   
    \- save_details: file saving details \(folder, subfolder, filename\)

    Returns: plot figure \(plotly.graph_objects.figure\)

- _function_ **plot_point** \(df, x, y, names=None, show_labels=False, show_plot=False, save_plot=False, save_details=None\)

    Plot data points   
    \- df: dataframe   
    \- x: x-value column name   
    \- y: y-value column name   
    \- names: names of data points \(i.e. sample IDs\)   
    \- show_labels: whether to show the label of the points   
    \- show_plot: whether to display the plot   
    \- save_plot: whether to save the plot   
    \- save_details: file saving details \(folder, subfolder, filename\)

    Returns: plot figure \(plotly.graph_objects.figure\)

- _function_ **plot_save** \(fig, save_details\)

    Saves the plot   
    \- fig: figure object to be saved   
    \- save_details: file saving details \(folder, subfolder, filename\)

    Returns: full filepath of the saved plot

- _function_ **plot_scatter** \(df, x, y, title=None, x_title=None, y_title=None, names=None, symbol=None, symbol_sequence=None, show_plot=False, save_plot=False, save_details=None\)

    Plot data points as a scatter   
    \- df: dataframe   
    \- x: x-value column name   
    \- y: y-value column name   
    \- title: title of plot   
    \- x_title: horizontal axis title   
    \- y_title: vertical axis title   
    \- names: names of data points \(i.e. sample IDs\)   
    \- symbol: column name to have different symbols   
    \- symbol_sequence: list of sybmols to use   
    \- show_plot: whether to display the plot   
    \- save_plot: whether to save the plot   
    \- save_details: file saving details \(folder, subfolder, filename\)

    Returns: plot figure \(plotly.graph_objects.figure\)
