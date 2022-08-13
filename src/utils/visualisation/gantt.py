# %%
import sys
sys.path.append('../')
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

from plotting.colours import get_palette, set_template

def main():
    config = pd.read_excel('config/config.xlsx', None)
    log_folder = 'logs/'
    log_output, tool_log = read_log(log_folder + 'activity_log.txt', config['connects'])
    gantt_plotter(log_output, tool_log, log_folder, show_plot=True, save_plot='svg')
    return
    
def read_log(activity_log, connects):
    '''
    Reads the log files and separate lines by tools
    - activity_log: file path of log file
    - connects: connection information about the devices / tools

    Returns: list of lines in log file, dictionary of logs for each tool
    '''
    with open(activity_log, 'r') as f:
        log_output = f.readlines()
    tools = connects.description.to_list()
    tool_log = {tool: [] for tool in tools}
    for line in log_output:
        if 'CNC align' in line:
            tool_log['cnc'].append(line)
        elif 'Syringe' in line:
            tool_log['pump'].append(line)
        elif 'Spinner' in line:
            order = line.split()[3].replace(':', '')
            tool_log[f'spin_{order}'].append(line)
    return log_output, tool_log

def gantt_plotter(log_output, tool_log, folder='logs/', show_plot=False, save_plot=None):
    '''
    Plots the gantt chart using the log files, in relative time
    - log_output: list of lines in log file
    - tool_log: dictionary of logs for each tool
    - show_plot: whether to show the gantt chart
    - save_plot: whether to save the gantt chart

    Returns: plot figure (plotly.graph_objects.figure)
    '''
    palette = get_palette(len(tool_log))
    spin_palette = palette[2:]
    spin_palette.reverse()
    palette = palette[:2] + spin_palette
    set_template(palette=palette)

    log_dfs = {}
    start_time = log_output[0].split()[0]
    start_time = datetime.strptime(start_time, '%H:%M:%S')
    for k, v in tool_log.items():
        times = []
        tasks = []
        for l in v:
            time_from_start = datetime.strptime(l.split()[0], '%H:%M:%S') - start_time
            time_from_start_s = time_from_start.total_seconds()
            if time_from_start_s < 0:
                time_from_start_s += 24*60*60
            times.append(time_from_start_s)
            tasks.append(' '.join(l.split()[4:]))
        df = pd.DataFrame({'time': times, 'task': tasks})
        df_start = df.iloc[::2]
        df_end = df.iloc[1::2]
        df_start.reset_index(inplace=True, drop=True)
        df_end.reset_index(inplace=True, drop=True)
        df = df_start.merge(df_end, left_index=True, right_index=True, suffixes=['_start', '_end'])
        df['duration'] = abs(df['time_end'] - df['time_start'])
        df['description'] = df['task_start'] + ' (' + df['duration'].astype(str) + 's)'
        df['tool'] = k
        log_dfs[k] = df

    fig = go.Figure(
        layout = {
            'barmode': 'stack',
            'xaxis': {'automargin': True},
            'yaxis': {'automargin': True, 'categoryorder': 'category ascending'}}
    )

    for tool, tool_df in log_dfs.items():
        fig.add_bar(x=tool_df['duration'],
                    y=tool_df['tool'],
                    base=tool_df['time_start'],
                    hovertext=tool_df['description'],
                    orientation='h',
                    showlegend=False,
                    name=tool)
    if show_plot:
        fig.show()
    if save_plot == 'html':
        fig.write_html(folder + 'gantt chart.html')
    elif save_plot == 'svg':
        fig.write_image(folder + 'gantt chart.svg')
    return fig

if __name__ == '__main__':
    main()

# %%
