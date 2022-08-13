# %%
import plotly.graph_objects as go
import plotly.io as pio

import plotly.colors

def get_continuous_color(colorscale, intermed):
    # From StackOverflow
    """
    Plotly continuous colorscales assign colors to the range [0, 1]. This function computes the intermediate
    color for any value in that range.

    Plotly doesn't make the colorscales directly accessible in a common format.
    Some are ready to use:
    
        colorscale = plotly.colors.PLOTLY_SCALES["Greens"]

    Others are just swatches that need to be constructed into a colorscale:

        viridis_colors, scale = plotly.colors.convert_colors_to_same_type(plotly.colors.sequential.Viridis)
        colorscale = plotly.colors.make_colorscale(viridis_colors, scale=scale)

    :param colorscale: A plotly continuous colorscale defined with RGB string colors.
    :param intermed: value in the range [0, 1]
    :return: color in rgb string format
    :rtype: str
    """
    if len(colorscale) < 1:
        raise ValueError("colorscale must have at least one color")

    if intermed <= 0 or len(colorscale) == 1:
        return colorscale[0][1]
    if intermed >= 1:
        return colorscale[-1][1]

    for cutoff, color in colorscale:
        if intermed > cutoff:
            low_cutoff, low_color = cutoff, color
        else:
            high_cutoff, high_color = cutoff, color
            break

    # noinspection PyUnboundLocalVariable
    return plotly.colors.find_intermediate_color(
        lowcolor=low_color, highcolor=high_color,
        intermed=((intermed - low_cutoff) / (high_cutoff - low_cutoff)),
        colortype="rgb")


def get_palette(n_colours=10, hex_type=True):
    viridis_colours, scale = plotly.colors.convert_colors_to_same_type(plotly.colors.sequential.Viridis)
    colourscale = plotly.colors.make_colorscale(viridis_colours, scale=scale)
    palette = []
    def rgb_to_hex(rgb):
        return '#%02x%02x%02x' % rgb
    for n in range(n_colours):
        if n_colours == 1:
            n_colours += 1
        colour = get_continuous_color(colourscale, n/(n_colours-1))
        if hex_type:
            rgb_val = tuple(int(round(float(s))) for s in colour[4:-1].split(', '))
            colour = rgb_to_hex(rgb_val)
        palette.append(colour)
    return palette


def set_template(template=None, n_colours=10, palette=None):
    '''Set Plotly Template'''
    if template == None:
        template = 'plotly_white+Viridis'
        if palette == None:
            palette = get_palette(n_colours)
        pio.templates['Viridis'] = go.layout.Template(
            layout=go.Layout(colorway=palette)
        )
    pio.templates.default = template
    return


def update_colours(fig):
    palette = get_palette(len(fig.data))
    for n, colour in enumerate(palette):
        fig.data[n]['line']['color'] = colour
        fig.data[n]['marker']['color'] = colour
    return fig

# %%
