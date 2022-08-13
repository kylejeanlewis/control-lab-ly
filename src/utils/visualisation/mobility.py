# %%
import numpy as np
import pandas as pd

"""Mobility functions"""
def get_oxide_capacitance(t_ox=285E-9, e_r=3.9):
	E_0 = 8.854E-12
	c_ox = E_0 * e_r / t_ox
	return c_ox

def get_derivative(x, y, order=1):
	if len(x) != len(y):
		print("Ensure x and y are of the same length!")
		return
	for _ in range(order):
		x, y = x, np.gradient(y, x)
	return x, y

def calc_mobility1(df, length, width=1E-3, v_gs=30, v_ds=4):
	c_ox = get_oxide_capacitance()
	x_ = df['Appl_Vd'].to_numpy()
	y_ = df[f'{v_gs}V_Id'].to_numpy()
	slope, intercept = np.polyfit(x_[:6], y_[:6], 1)
	dx2, d2y = get_derivative(x_, y_, order=2)
	dx2, d2y = pd.Series(dx2), pd.Series(d2y)
	v_t = dx2[d2y.idxmax()]
	length *= 1E-6
	mob_eff = abs((length/width) * (slope/(c_ox*(v_gs - v_t - v_ds))) * 10000)
	return mob_eff

def calc_mobility2(df, length, width=1E-3, v_ds=4):
	c_ox = get_oxide_capacitance()
	x_ = df['Appl_Vg'].to_numpy()
	y_ = df[f'{v_ds}V_Id'].to_numpy()
	slope, intercept = np.polyfit(x_[:6], y_[:6], 1)
	length *= 1E-6
	mob_eff = abs((length/width) * (slope/(c_ox*v_ds)) * 10000)
	return mob_eff

def calc_mobility3(df, length, width=1E-3, v_ds=10):
	c_ox = get_oxide_capacitance()
	x_ = df['Appl_Vg'].to_numpy()
	y_ = df[f'{v_ds}V_Id'].to_numpy()
	x, g_m = get_derivative(x_, y_, order=1)
	g_m = abs(g_m)
	length *= 1E-6
	mob_fe = abs((length/width) * (g_m/(c_ox*v_ds)) * 10000)
	# pdf = pd.DataFrame({'Vg': x, 'Mobility': mob_fe})
	# fig = px.line(pdf, 'Vg', 'Mobility')
	# fig.show()
	return mob_fe.mean()

def calc_mobility4(df, length, width=1E-3, v_ds=10):
	c_ox = get_oxide_capacitance()
	x_ = df['Appl_Vg'].to_numpy()
	y_ = df[f'{v_ds}V_Id'].to_numpy()
	x, g_m = get_derivative(x_, y_, order=1)
	g_m = abs(g_m)
	slope, intercept = np.polyfit(x[:6], g_m[:6], 1)
	length *= 1E-6
	mob_fe_sat = abs((length/width) * (slope/c_ox) * 10000)
	
	# pdf = pd.DataFrame({'v_gs': x, 'G_m': y, 'fit': np.array(x)*slope+intercept})
	# fig = px.line(pdf, x='v_gs', y=['G_m', 'fit'])
	# fig.show()
	# print('Low-field mobility: {:.3e} cm^2 / (Vs)'.format(mob_fe_sat))
	return mob_fe_sat

def calc_mobility5(df, length, width=1E-3, v_ds=4):
	c_ox = get_oxide_capacitance()
	x_ = df['Appl_Vg'].to_numpy()
	y_ = df[f'{v_ds}V_Id'].to_numpy()
	x, g_m = get_derivative(x_, y_, order=1)
	g_m = abs(g_m)
	y = y_ / (g_m**0.5)
	slope, intercept = np.polyfit(x, y, 1)
	length *= 1E-6
	mob_low = (length/width) * (slope**2) / (c_ox * v_ds) * 10000
	
	# pdf = pd.DataFrame({'v_gs': x, 'Y': y, 'fit': np.array(x)*slope+intercept})
	# fig = px.line(pdf, x='v_gs', y=['Y', 'fit'])
	# fig.show()
	# print('Low-field mobility: {:.3e} cm^2 / (Vs)'.format(mob_low))
	return mob_low

def calc_mobility6(df, length, width=1E-3, v_ds=10):
	c_ox = get_oxide_capacitance()
	x = df['Appl_Vg'].to_numpy()
	y = np.sqrt(df[f'{v_ds}V_Id']) if f'{v_ds}V_Id' in df.columns else df[f'{v_ds}V_Id_sqrt']
	slope, intercept = np.polyfit(x[:6], y[:6], 1)
	length *= 1E-6
	mob_sat = (2*length/width) * (slope**2) / c_ox * 10000
	
	# print('Saturation mobility: {:.3e} cm^2 / (Vs)'.format(mob_sat))
	return mob_sat

def get_mobility(df, name, title, width=1E-3, mob_type=6):
	global mobility
	mobility_types = {
		1: 'effective_1',
		2: 'effective_2',
		3: 'field-effect (lin)',
		4: 'field-effect (sat)',
		5: 'low-field',
		6: 'saturation'
	}
	length = int(title.split('um')[0][-2:])
	mob_funcs = {
		1: calc_mobility1,
		2: calc_mobility2,
		3: calc_mobility3,
		4: calc_mobility4,
		5: calc_mobility5,
		6: calc_mobility6
	}
	mob_func = mob_funcs[mob_type]
	mob = mob_func(df, length, width)
	anneal = True if name.endswith('_2') else False
	mobility.append({
		'sample': name, 
		'length': length, 
		'mobility': mob, 
		'type': mobility_types[mob_type], 
		'anneal': anneal,
		'device': title.split()[2]
		})
	return

def get_mobilities(df, name, title, width=1E-3, mob_types=[2,3,4,5,6], mob_list=[]):
	global mobility
	mobility = mob_list
	for mob_type in mob_types:
		pass
		get_mobility(df, name, title, width, mob_type)
	return
