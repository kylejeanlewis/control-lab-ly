# %%
from filesearch import get_basedir, locate_paths

# Only edit this code block to generate visualisations
base_dir = get_basedir(r'\A STAR\QD cocktail party - General')
data_dir = base_dir + r'\Characterisation'
logs_dir = base_dir + r'\Experiment logs'
sample_ids_of_interest = ['G001', 'G002', 'G003', 'G004']
use_demo_samples = True
do_list = ['FET', 'FTIR', 'PESA', 'HSI', 'spin curve']
to_do = [True, False, False, False, False]


'''FET processing'''
if to_do[do_list.index('FET')]:
    import FET
    DEMO = ['R012_1']
    if use_demo_samples:
        sample_ids_of_interest = DEMO
    channel_lengths = [80,60,30,80,40,30,50,40,60,50]
    width = 18.23E-3
    chip_size = (1,1)
    relevant_paths = locate_paths(data_dir, '\\Primitiv', sample_ids_of_interest, 'folder')
    FET.process(relevant_paths, FET.FET_grid, channel_lengths, width, chip_size=chip_size, interval=5, y_axis=['Id', 'Id'])


'''FTIR processing'''
if to_do[do_list.index('FTIR')]:
    import FTIR
    DEMO = ['Q025', 'Q026', 'Q027', 'Q028']
    if use_demo_samples:
        sample_ids_of_interest = DEMO
    relevant_paths = locate_paths(data_dir, '\\FTIR', sample_ids_of_interest, 'file', '.csv')
    FTIR.process(relevant_paths, FTIR.FTIR, data_dir+'\\FTIR')


'''PESA processing'''
if to_do[do_list.index('PESA')]:
    import PESA
    DEMO = ['Q025', 'Q026', 'Q027', 'Q028']
    if use_demo_samples:
        sample_ids_of_interest = DEMO
    relevant_paths = locate_paths(data_dir, '\\PESA', sample_ids_of_interest, 'file', '.csv')
    PESA.process(relevant_paths, PESA.PESA)


'''HSI processing'''
if to_do[do_list.index('HSI')]:
    import HSI
    DEMO = ['G001', 'G002', 'G003', 'G004', 'G005', 'G006']
    if use_demo_samples:
        sample_ids_of_interest = DEMO
    batch_ids_of_interest = ['BG001']
    relevant_paths = locate_paths(data_dir, '\\HSI', batch_ids_of_interest, 'file', '.txt')
    HSI.process(relevant_paths, HSI.HSI, sample_ids_of_interest)


''' Spin curve processing'''
if to_do[do_list.index('spin curve')]:
    import calibration
    DEMO = ['G001', 'G002', 'G003', 'G004']
    if use_demo_samples:
        sample_ids_of_interest = DEMO
    relevant_paths = locate_paths(data_dir, '\\Profilometry', sample_ids_of_interest, 'file', '.txt')
    calibration.process(relevant_paths, calibration.SpeedCollection, sample_ids_of_interest, 30, logs_dir)

# %%
