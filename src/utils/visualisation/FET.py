# %%
import sys
sys.path.append('../')
import os
import numpy as np
import pandas as pd
import plotly.express as px
from plotting.plotters import plot_line, plot_combined, update_colours
from mobility import get_mobilities

global mobility, device_summaries
mobility = []
device_summaries = True

def main():
	from filesearch import get_basedir, locate_paths
	global sample_ids_of_interest
	base_dir = get_basedir(r'\A STAR\QD cocktail party - General')
	main_dir = base_dir + r'\Characterisation\Primitiv'
	sample_ids_of_interest = ['sio2_D']
	# for inter-digiated pattern
	# channel_lengths = [50]
	# width = 18.23E-3
	# chip_size = (1,1)
	# for regular 1mm width pattern
	# channel_lengths = [80,60,30,80,40,30,50,40,60,50]
	channel_lengths = [80,60,30,80]#,40,30,50,40]
	width = 1E-3
	chip_size = (2,2)
	
	global mobility, device_summaries
	mobility = []
	device_summaries = True
	relevant_paths = locate_paths(main_dir, '', sample_ids_of_interest, 'folder')
	process(relevant_paths, FET_grid, channel_lengths, width, chip_size=chip_size, interval=5, y_axis=['Id', 'Id'], save_csv=False)

	mob_df = pd.DataFrame(mobility)
	return mob_df


def read_data(save_details):
	'''
	Read the processed data files
	- save_details: the details on the folder, subfolder, and format of the saved files

	Returns: {idvd_filnames: pd.Dataframe}, {idvg_filnames: pd.Dataframe}, [labels]
	'''
	data = pd.DataFrame()
	results_idvd = {}
	results_idvg = {}

	path = save_details['folder']
	result_folder_path = path + save_details['subfolder']
	file_format = save_details['format']

	labels = []
	curve_types = ['Id-Vd', 'Id-Vg']

	for label in range(1, 100):
		labels.append(label)
		for curve_type in curve_types:
			formatted = file_format.format(label=label, curve_type=curve_type, connect='')
			full_path = result_folder_path + formatted

			if os.path.isfile(full_path):
				data = pd.read_csv(full_path)
				if curve_type == 'Id-Vd':
					results_idvd[formatted] = data
				else:
					results_idvg[formatted] = data
			else:
				labels.remove(label)
				break
		
	return results_idvd, results_idvg, labels


def extract_data(save_details, param_list, interval=1, save_data=True):
	'''
	Function for extracting data from result's csv files
	- save_details: the details on the folder, subfolder, and format of the saved files
	- param_list: list of voltage parameters / settings
	- interval: size of data reading window
	- save_data: whether to save the processed data

	Returns: {idvd_filnames: pd.Dataframe}, {idvg_filnames: pd.Dataframe}, [labels]
	'''
	results_idvd = {}
	results_idvg = {}
	labels = []
	curr_label = 1
	results_idvd, results_idvg, labels = read_data(save_details)
	if len(results_idvd) and len(results_idvg) and len(labels):
		return results_idvd, results_idvg, labels

	path = save_details['folder']
	result_folder_path = path + save_details['subfolder']
	file_format = save_details['format']

	volts_G_out, volts_SD_out, volts_G_trans, volts_SD_trans = param_list
	applied_V_out = pd.DataFrame(np.array(np.meshgrid(volts_G_out, volts_SD_out)).T.reshape(-1,2), columns=["Appl_Vg", "Appl_Vd"])
	applied_V_trans = pd.DataFrame(np.array(np.meshgrid(volts_SD_trans, volts_G_trans)).T.reshape(-1,2), columns=["Appl_Vd", "Appl_Vg"])

	curve_types = ['Id-Vd', 'Id-Vg']
	connects = ['G', 'SD']
	data = pd.DataFrame()

	if not os.path.exists(result_folder_path):
		os.makedirs(result_folder_path)

	while True:
		skip_label = False
		for curve_type in curve_types:
			data_fin = pd.DataFrame()
			for connect in connects: 
				formatted = file_format.format(label=curr_label, curve_type=curve_type, connect=connect)
				full_path = path + formatted

				if os.path.isfile(full_path):
					data = pd.read_csv(full_path)
					data = data.groupby(np.arange(len(data))//interval).mean()
					data = data.iloc[:, [1,2]]

					if curve_type == 'Id-Vg' and connect == "SD":
						data_sqrt = np.sqrt(data[["Id"]].apply(abs))
						data_log10 = np.log10(data[["Id"]].apply(abs))

						data_sqrt.rename(columns={"Id" : "Id_sqrt"}, inplace=True)
						data_log10.rename(columns={"Id" : "Id_log10"}, inplace=True)

						data_sqrt.reset_index(drop=True, inplace=True)
						data_log10.reset_index(drop=True, inplace=True)
						data = pd.concat([data, data_log10, data_sqrt], axis = 1)

					data_fin.reset_index(drop = True, inplace=True)
					data.reset_index(drop = True, inplace=True)
					data_fin = pd.concat([data_fin, data], axis = 1)

				elif curr_label < 100:
					curr_label += 1
					skip_label = True
					break
				else:
					return results_idvd, results_idvg, labels
			if skip_label:
				break
			
			if curve_type == 'Id-Vg':
				data_fin = pd.concat([applied_V_trans, data_fin], axis = 1)

				data_net_current = data_fin["Id"] - data_fin['Ig']
				data_net_current.rename("Id_net", inplace=True)
				data_net_current.reset_index(drop=True, inplace=True)
				data_sqrt = np.sqrt(data_net_current.apply(abs))
				data_log10 = np.log10(data_net_current.apply(abs))

				data_sqrt.rename("Id_net_sqrt", inplace=True)
				data_log10.rename("Id_net_log10", inplace=True)

				data_sqrt.reset_index(drop=True, inplace=True)
				data_log10.reset_index(drop=True, inplace=True)
				data_fin = pd.concat([data_fin, data_net_current, data_log10, data_sqrt], axis = 1)

				results_idvg[formatted] = data_fin

			else:
				data_fin = pd.concat([applied_V_out, data_fin], axis = 1)

				data_net_current = data_fin["Id"] - data_fin['Ig']
				data_net_current.rename("Id_net", inplace=True)
				data_net_current.reset_index(drop=True, inplace=True)
				data_fin = pd.concat([data_fin, data_net_current], axis = 1)

				results_idvd[formatted] = data_fin

			if save_data:
				data_fin.to_csv(result_folder_path + file_format.format(label=curr_label, curve_type=curve_type, connect=''))
			
		if skip_label:
			continue

		labels.append(curr_label)
		curr_label += 1


def process(all_paths, measurement_object, channel_lengths, width, chip_size=(5,2), interval=1, y_axis=["Id", "Id_log10"], save_csv=False):
	'''
    Main function to process the data and generate the visualisation
    - all_paths: dictionary of all the filepaths
    - measurement_object: the class used to handle the data
    - channel_lengths: channel_lengths for different devices
	- interval: size of data reading window
	- y_axis: the y-values to plot for respective graphs
	- save_csv: whether to save the processed data

    Returns: {sample_ids: FET_grid} or None
    '''
	global channel_width
	channel_width = width
	if len(all_paths):
		sample_ids = []
		sample_paths = []
		for sample_id, paths in all_paths.items():
			sample_ids.append(sample_id)
			sample_paths = sample_paths + [p for _, p in paths.items()]

		samples = {}
		for s, sample_dir in enumerate(sample_paths):
			params = {}
			with open(sample_dir+'\\parameters.txt') as f:
				for line in f:
					(key, val) = line.split(': ')
					key = key.lower()
					val = val[1:-2].split(',')
					params[key] = np.arange(*[int(v) for v in val]).tolist()
			param_list = [params['idvd_g'], params['idvd_d'], params['idvg_g'], params['idvg_d']]
			save_details = {
				'folder': sample_dir,
				'subfolder': '\\RESULTS\\csv',
				'format': r'\Device C{label} {curve_type}, {connect}.csv' }
			sample_idvd, sample_idvg, sample_labels = extract_data(
				save_details=save_details,
				param_list=param_list,
				interval=interval,
				save_data=True )

			sample_labels = [f'{str(sample_labels[l])} ({str(channel_lengths[l])}um)' for l in range(len(sample_labels))]

			sample = measurement_object(
				name=sample_ids[s],
				datasets={'Id-Vd': sample_idvd, 'Id-Vg': sample_idvg},
				path=sample_dir,
				labels=sample_labels,
				volt_var=[params['idvd_d'], params['idvg_g']], 
				volt_const=[params['idvd_g'], params['idvg_d']], 
				x_axis=["Appl_Vd", "Appl_Vg"],
				y_axis=y_axis )
			sample.plot_grid(chip_size=chip_size)
			sample.plot_individual(save_plot=True, save_parse=save_csv)
			samples[sample_ids[s]] = sample
		return samples
	else:
		print("No files found!")
	return


"""Plot device"""
def get_device_summaries(name, device, length, path):
	import plotly.express as px
	big_title = f'{name} Device C{device} {length}'
	figs_all = []
	if not os.path.exists(f'{path}\\RESULTS\\device'):
		os.makedirs(f'{path}\\RESULTS\\device')

	filenames = [f'Device C{device} Id-Vd, .csv', f'Device C{device} Id-Vg, .csv']
	for filename in filenames:
		x = 'Vd' if 'Vd' in filename else 'Vg'
		const = 'Vd' if 'Vg' in filename else 'Vg'
		ys = ['Id', 'Ig']
		df = pd.read_csv(f'{path}\\RESULTS\\csv\\{filename}')
		figs = []
		titles = []

		for y in ys:
			title = f'Device C{device} {length} {y}-{x}'
			fig = px.line(df, x=f'Appl_{x}', y=y, color=f'Appl_{const}')
			fig.update_layout(
				title_text=title,
				xaxis_title=x,
				yaxis_title=y
			)
			fig = update_colours(fig)
			# fig.write_image(f'{path}\\RESULTS\\device\\{title}.svg')
			fig.write_html(f'{path}\\RESULTS\\device\\{title}.html')
			figs.append(fig)
			titles.append(f'{y}-{x}')
		
		save_details = {
			'folder': path,
			'format': f'\\device\\{name} Device C{device}_{x}.html',
			'name': ''}
		big_fig = plot_combined(figs, 'V', 'I', dimension=(2,1), main_title=big_title+' '+x,
			subplot_titles=titles, show_plot=False, save_plot=False, save_details=save_details)
		# big_fig.write_image(f'{path}\\RESULTS\\device\\{big_title}.svg')
		big_fig.write_html(f'{path}\\RESULTS\\device\\{big_title+x}.html')
		figs_all.append(big_fig)

	return figs_all


class FET_grid(object):
	"""
	'FET_grid' class contains methods to create a collection of FET_single objects, as well as to generate grid plots and
	individual plots for each device.
	"""
	def __init__(self, name, datasets, path, labels, volt_var, volt_const, x_axis, y_axis):
		self.name = name
		self.datasets = datasets
		self.path = path
		self.labels = labels

		self.volt_consts = volt_const
		self.volt_vars = volt_var
		self.xs = x_axis
		self.ys = y_axis

		self.parsed_data = pd.DataFrame()
		self.collection = {}
		self.create_collection()
		return


	def create_collection(self):
		'''
		Creates a collection of FET_single objects

		Returns: list of FET_single objects
		'''
		for j, (plot_type, dataset) in enumerate(self.datasets.items()):
			x = self.xs[j]
			y = self.ys[j]
			volt_const = self.volt_consts[j]
			volt_var = self.volt_vars[j]
			self.collection[plot_type] = FET_single(self.name, dataset, self.path, self.labels, volt_var, volt_const, x, y, channel_width)
		return self.collection


	def plot_grid(self, chip_size=(4,2)):
		'''
		Generates a grid plot of devices on the chip
		- chip_size: dimensions of the layout of the devices

		Returns: plot figure (plotly.graph_objects.figure)
		'''
		subplot_titles = ["Device C{}".format(self.labels[c]) for c in range(0,chip_size[0]*chip_size[1])]
		big_figs = {}
		for plot_type, fet in self.collection.items():
			title = self.name +  ' (' + plot_type + ')'
			figs = []
			for chip_label, (_, df) in enumerate(fet.dataset.items()):
				fig = fet.plot(df, title=chip_label+1)
				figs.append(fig)
			
			save_details = {
				'folder': fet.path,
				'format': '\\{} Grid plot.html',
				'name': title }
			big_fig = plot_combined(figs, fet.x, fet.y, dimension=chip_size, main_title=title,
				subplot_titles=subplot_titles, show_plot=True, save_plot=True, save_details=save_details)
			big_figs[plot_type] = big_fig
		return big_figs


	def plot_individual(self, save_plot=False, save_parse=False):
		'''
		Generates a individual plots for devices on the chip
		- save_plot: whether to save the plots
		- save_parse: whether to save the parsed data from the operation

		Returns: None
		'''
		for _, fet in self.collection.items():
			fet.plot_all(save_plot=save_plot, save_parse=save_parse)
		return


class FET_single(object):
	"""
	'FET_single' class contains methods to parse the data and plot them, as well as to perform multiple parse and plot operations.
	"""
	def __init__(self, name, dataset, path, labels, volt_var, volt_const, x_axis, y_axis, channel_w=1E-3):
		self.name= name
		self.dataset = dataset
		self.path = path
		self.labels = labels
		self.volt_const = volt_const
		self.volt_var = volt_var
		self.x = x_axis
		self.y = y_axis
		self.parsed_data = pd.DataFrame()
		self.channel_width = channel_w
		return


	def parse(self, df, title, save_parse=False):
		'''
		Parse data from csv files to get a table that is suitable for plotting
		- df: dataframe read from csv file
		- title: filename for parsed data
		- save_parse: whether to save parsed data

		Returns: None
		'''
		self.parsed_data = pd.DataFrame()
		new_x, new_y = self.x, "{label}V_"+self.y
		for ind, volt_c in enumerate(self.volt_const):
			if ind == 0:
				interval = df[[self.x, self.y]].iloc[ind*len(self.volt_var):(ind+1)*len(self.volt_var), :]
				interval.rename(columns = {self.x: new_x, self.y: new_y.format(label=volt_c)}, inplace=True)
			else:
				interval = df[self.y].iloc[ind*len(self.volt_var):(ind+1)*len(self.volt_var)]
				interval.rename(new_y.format(label=volt_c), inplace=True)

			interval.reset_index(drop=True, inplace=True)
			self.parsed_data.reset_index(drop=True, inplace=True)
			self.parsed_data = pd.concat([self.parsed_data, interval], axis=1)
		
		if save_parse:
			save_details = {
				'folder': self.path + '\\RESULTS\\csv',
				'format': '\\parsed_{}.csv',
				'name': title }
			filepath = save_details['folder'] + save_details['format'].format(save_details['name'])
			self.parsed_data.to_csv(filepath)
		return


	def parse_all(self, save_parse=False):
		'''
		Parse data from multiple csv files to get tables that are suitable for plotting
		- save_parse: whether to save parsed data

		Returns: None
		'''
		for ind, (_, df) in enumerate(self.dataset.items()):
			title = self.name + ' Device C' + str(self.labels[ind]) + ' ' + self.x + '-' + self.y
			self.parse(df, title=title, save_parse=save_parse)
		return


	def plot(self, df, title, show_plot=False, save_plot=False, save_parse=False):
		'''
		Plots data from csv files after being parsed
		- df: dataframe read from csv file
		- title: title of plot
		- show_plot: whether to display the plot
		- save_plot: whether to save the plot
		- save_parsed: whether to save parsed data

		Returns: plot figure (plotly.graph_objects.figure)
		'''
		self.parse(df, title, save_parse)
		y_list = self.parsed_data.columns.to_list()
		y_list.remove(self.x)
		save_details = {
			'folder': self.path,
			'format': '\\{}.html',
			'name': title }
		fig = plot_line(self.parsed_data, x=self.x, y=y_list, 
			title=title, x_title=self.x, y_title=self.y,
			show_plot=show_plot, save_plot=save_plot, save_details=save_details)
		
		if type(title) == str and 'Appl_Vg' in title:
			# get_mobilities(self.parsed_data, self.name, title, self.channel_width, mob_list=mobility)
			pass
		if type(title) == str and 'Appl_Vd' in title:
			# get_mobilities(self.parsed_data, self.name, title, self.channel_width, mob_types=[1], mob_list=mobility)
			pass
		return fig


	def plot_all(self, save_plot=False, save_parse=False):
		'''
		Plots data from csv files after being parsed
		- save_plot: whether to save the plot
		- save_parsed: whether to save parsed data

		Returns: None
		'''
		for ind, (_, df) in enumerate(self.dataset.items()):
			title = self.name + ' Device C' + str(self.labels[ind]) + ' ' + self.x + '-' + self.y
			self.plot(df, title=title, save_plot=save_plot, save_parse=save_parse)
			device = str(self.labels[ind]).split()[0]
			length = str(self.labels[ind]).split()[1]
			try:
				if device_summaries:
					get_device_summaries(self.name, device, length, self.path)
			except:
				pass

		return


if __name__ == '__main__':
	mob_df = main()

# %%
if __name__ == '__main__':
	"""Compare mobilities - across samples"""
	mob_filename = 'Mobilities - ' + sample_ids_of_interest[0]
	mob_df.to_csv(f'C://Users//leongcj//Desktop//{mob_filename}.csv')
	import plotly.express as px
	fig = px.scatter(
		mob_df, x='length', y='mobility', color='type', symbol='type', hover_data=['anneal', 'device'],
		labels={
			'length': 'Channel length [ um ]',
			'mobility': 'Mobility [ cm^2 / (Vs) ]',
			'sample': 'Sample',
			'anneal': 'Anneal'
		}
	)
	fig.update_layout(
		title=mob_filename,
		yaxis={
			'showexponent':'all', 
			'exponentformat':'e', 
			'minexponent':2
			}
		)
	fig.show()
	fig.write_html(r'C:\Users\leongcj\Desktop' + f'\\{mob_filename}.html')
# %%
