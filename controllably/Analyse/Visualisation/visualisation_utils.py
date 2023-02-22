# %% -*- coding: utf-8 -*-
"""
Created on Fri 2023/01/06 09:00:00
@author: Chang Jie

Notes / actionables:
-
"""
# Third party imports
from dash import Dash, dcc, html

# Local application imports
print(f"Import: OK <{__name__}>")

class Visualiser(object):
    def __init__(self):
        self.graphs = []
        pass
    
    def addGraph(self, graph):
        self.graphs.append(graph)
        return
    
    @staticmethod
    def display(graphs:list):
        app = Dash()
        app.layout = html.Div(
            [dcc.Graph(figure=fig) for fig in graphs]
        )

        app.run_server(debug=True, use_reloader=False)
        return
    
    def displayGraphs(self):
        return self.display(self.graphs)

VIZ = Visualiser()
"""Visualizer instance to plot graphs in browser"""
