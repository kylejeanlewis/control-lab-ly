# %%
import os
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp

from plotting.colours import set_template, update_colours
set_template()

def plot_add_point(fig, x_coord, y_coord, name, text, mode, text_position, show_plot=False, save_plot=False, save_details=None):
    '''
    Adds point(s) to existing figure object
    - fig: figure object
    - x_coord: x-coordinate(s)
    - y_coord: y-coordinate(s)
    - name: name(s) of point(s) / legend
    - text: text label(s)
    - mode: type of plotting mode (i.e. with or without text)
    - text_position: position text label for point(s)
    - show_plot: whether to display the plot
    - save_plot: whether to save the plot
    - save_details: file saving details (folder, subfolder, filename)

    Returns: plot figure (plotly.graph_objects.figure)
    '''
    fig.add_trace(go.Scatter(
            x=x_coord,
            y=y_coord,
            name=name,
            text=text,
            mode=mode,
            textposition=text_position
        ))
    fig = update_colours(fig)
    if show_plot:
        fig.show()
    if save_plot:
        plot_save(fig, save_details)
    return fig


def plot_add_line(fig, x_data, y_data, name, show_plot=False, save_plot=False, save_details=None):
    '''
    Adds a line to existing figure object
    - fig: figure object
    - x_data: x-coordinates
    - y_data: y-coordinates
    - name: name of line / legend
    - show_plot: whether to display the plot
    - save_plot: whether to save the plot
    - save_details: file saving details (folder, subfolder, filename)

    Returns: plot figure (plotly.graph_objects.figure)
    '''
    fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data,
            name=name,
            mode='lines'
        ))
    fig = update_colours(fig)
    if show_plot:
        fig.show()
    if save_plot:
        plot_save(fig, save_details)
    return fig


def plot_add_subplot(big_fig, fig, position, x_title, y_title):
    '''
    Adds a single figure to existing grid
    - big_fig: grid plot object
    - fig: figure object
    - position: position in grid to add the figure
    - x_title: horizontal axis title
    - y_title: vertical axis title

    Returns: plot figure (plotly.graph_objects.figure)
    '''
    # For as many traces that exist per Express figure, get the traces from each plot and store them in an array.
    # This is essentially breaking down the Express fig into its traces
    fig_traces = []
    for trace in range(len(fig["data"])):
        fig_traces.append(fig["data"][trace])

    # Get the Express fig broken down as traces and add the traces to the proper plot within in the subplot
    for traces in fig_traces:
        big_fig.append_trace(traces, row=position[0], col=position[1])
    
    big_fig.update_xaxes(title_text=x_title, row=position[0], col=position[1])
    big_fig.update_yaxes(title_text=y_title, row=position[0], col=position[1])
    return big_fig


def plot_blank_grid(dimension, main_title, subplot_titles, h_space=0.1, v_space=0.15):
    '''
    Initialise / create new blank grid plot object
    - dimension: size of grid
    - main_title: overall title of grid plot
    - subplot_titles: titles of individual subplots
    - h_space: horizontal spacing between subplots
    - v_space: vertical spacing between subplots

    Returns: plot figure (plotly.graph_objects.figure)
    '''
    big_fig = sp.make_subplots(
        rows=dimension[0], cols=dimension[1],
        subplot_titles=subplot_titles,
        horizontal_spacing = h_space,
        vertical_spacing = v_space
    )
    big_fig.update_layout(title_text=main_title)
    return big_fig


def plot_combined(figs, x_title, y_title, dimension, main_title, subplot_titles, h_space=0.1, v_space=0.15, show_plot=False, save_plot=False, save_details=None):
    '''
    Generate a combined grid plot
    - figs: list of figures to be added to grid
    - x_title: horizontal axis title
    - y_title: vertical axis title
    - dimension: size of grid
    - main_title: overall title of grid plot
    - subplot_titles: titles of individual subplots
    - h_space: horizontal spacing between subplots
    - v_space: vertical spacing between subplots
    - show_plot: whether to display the plot
    - save_plot: whether to save the plot
    - save_details: file saving details (folder, subfolder, filename)

    Returns: plot figure (plotly.graph_objects.figure)
    '''
    big_fig = plot_blank_grid(dimension, main_title, subplot_titles, h_space, v_space)
    m = 1
    n = 1
    for fig in figs:
        plot_add_subplot(big_fig, fig, (m, n), x_title, y_title)
        n += 1
        if n > dimension[1]:
            m += 1
            n = 1

    if show_plot:
        big_fig.show()
    if save_plot:
        plot_save(big_fig, save_details)
    return big_fig


def plot_kinked_fit_points(df, x, y, title, x_title, y_title, data_plot_type='scatter', show_plot=False, save_plot=False, save_details=None):
    '''
    Plot data points with a fitted kinked line
    - df: dataframe
    - x: x-value column name
    - y: y-value column name
    - title: title of plot
    - x_title: horizontal axis title
    - y_title: vertical axis title
    - data_plot_type: scatter or line
    - show_plot: whether to display the plot
    - save_plot: whether to save the plot
    - save_details: file saving details (folder, subfolder, filename)

    Returns: plot figure (plotly.graph_objects.figure)
    '''
    if data_plot_type == 'scatter':
        fig = px.scatter(df, x, y)
    elif data_plot_type =='line':
        fig = px.line(df, x, y)
    if 'overall' in df.columns:
        fig.add_trace(go.Scatter(
            x=df[x],
            y=df['overall'],
            name="fitted",
            mode='lines',
        ))
    elif 'baseline' in df.columns or 'slope' in df.columns:
        try:
            fig2 = px.line(df, x, 'baseline')
            fig = go.Figure(data=fig.data + fig2.data)
        except:
            fig3 = px.line(df, x, 'slope')
            fig = go.Figure(data=fig.data + fig3.data)
        finally:
            pass
    fig.update_layout(
            title_text=title,
            xaxis_title=x_title,
            yaxis_title=y_title
        )
    fig = update_colours(fig)
    if show_plot:
        fig.show()
    if save_plot:
        plot_save(fig, save_details)
    return fig


def plot_line(df, x, y, title=None, x_title=None, y_title=None, names=None, line_width=None, show_plot=False, save_plot=False, save_details=None):
    '''
    Plot data points in a line
    - df: dataframe
    - x: x-value column name
    - y: y-value column name
    - title: title of plot
    - x_title: horizontal axis title
    - y_title: vertical axis title
    - names: names of data points (i.e. sample IDs)
    - line_width: width of line plot
    - show_plot: whether to display the plot
    - save_plot: whether to save the plot
    - save_details: file saving details (folder, subfolder, filename)

    Returns: plot figure (plotly.graph_objects.figure)
    '''
    fig = px.line(df, x, y, color=names)
    if line_width != None:
        fig.update_traces(line={'width': line_width})
    if title == None or x_title == None or y_title == None:
        pass
    else:
        fig.update_layout(
			title_text=title,
			xaxis_title=x_title,
			yaxis_title=y_title
		)
    fig = update_colours(fig)
    if show_plot:
        fig.show()
    if save_plot:
        plot_save(fig, save_details)
    update_colours(fig)
    return fig


def plot_line_point(line_df, point_df, x, y, title, x_title, y_title, names=None, line_width=None, show_plot=False, save_plot=False, save_details=None):
    '''
    Combine a line plot and a scatter plot
    - line_df: dataframe for line plot
    - point_df: dataframe for scatter plot
    - x: x-value column name
    - y: y-value column name
    - title: title of plot
    - x_title: horizontal axis title
    - y_title: vertical axis title
    - names: names of data points (i.e. sample IDs)
    - line_width: width of line plot
    - show_plot: whether to display the plot
    - save_plot: whether to save the plot
    - save_details: file saving details (folder, subfolder, filename)

    Returns: plot figure (plotly.graph_objects.figure)
    '''
    fig1 = plot_line(line_df, x, y, names=names, line_width=line_width)
    fig2 = plot_point(point_df, x, y, names=names)
    fig = go.Figure(data=fig2.data + fig1.data)
    fig.update_layout(
                title_text=title,
                xaxis_title=x_title,
                yaxis_title=y_title
            )
    fig = update_colours(fig)
    if show_plot:
        fig.show()
    if save_plot:
        plot_save(fig, save_details)
    return fig


def plot_point(df, x, y, names=None, show_labels=False, show_plot=False, save_plot=False, save_details=None):
    '''
    Plot data points
    - df: dataframe
    - x: x-value column name
    - y: y-value column name
    - names: names of data points (i.e. sample IDs)
    - show_labels: whether to show the label of the points
    - show_plot: whether to display the plot
    - save_plot: whether to save the plot
    - save_details: file saving details (folder, subfolder, filename)

    Returns: plot figure (plotly.graph_objects.figure)
    '''
    labels = None
    if show_labels:
        x_coord = df[x]
        labels = ["{:.0f}".format(n) for n in x_coord]
    fig = px.scatter(df, x, y, color=names, text=labels, symbol_sequence=['x'])
    fig.update_traces(textposition='bottom center')
    fig = update_colours(fig)
    if show_plot:
        fig.show()
    if save_plot:
        plot_save(fig, save_details)
    return fig


def plot_save(fig, save_details):
    '''
    Saves the plot
    - fig: figure object to be saved
    - save_details: file saving details (folder, subfolder, filename)

    Returns: full filepath of the saved plot
    '''
    results_folder = save_details['folder'] + '\\RESULTS'
    if not os.path.exists(results_folder):
            os.makedirs(results_folder)
    full_path = results_folder + save_details['format'].format(save_details['name'])
    fig.write_html(full_path)
    return full_path


def plot_scatter(df, x, y, title=None, x_title=None, y_title=None, names=None, symbol=None, symbol_sequence=None, show_plot=False, save_plot=False, save_details=None):
    '''
    Plot data points as a scatter
    - df: dataframe
    - x: x-value column name
    - y: y-value column name
    - title: title of plot
    - x_title: horizontal axis title
    - y_title: vertical axis title
    - names: names of data points (i.e. sample IDs)
    - symbol: column name to have different symbols
    - symbol_sequence: list of sybmols to use
    - show_plot: whether to display the plot
    - save_plot: whether to save the plot
    - save_details: file saving details (folder, subfolder, filename)

    Returns: plot figure (plotly.graph_objects.figure)
    '''
    fig = px.scatter(
        df, x, y, color=names, symbol=symbol, symbol_sequence=symbol_sequence, 
        title=title, labels={x: x_title, y: y_title}
    )
    fig.update_layout(legend=dict(
        orientation='h',
        xanchor="right",
        yanchor="bottom",
        x=1, y=1
    ))
    fig = update_colours(fig)
    if show_plot:
        fig.show()
    if save_plot:
        plot_save(fig, save_details)
    return fig


# %%
