# %% -*- coding: utf-8 -*-
"""
Created on Fri 2022/06/18 09:00:00
@author: Chang Jie

Notes / actionables:
-
"""

class CircuitDiagram(object):
    """
    Circuit diagram manipulator.
    """
    def __init__(self):
        return

    def drawCircuit(self, string:str, parallel_parts:dict, canvas_size=(0,0), pad=5):
        """
        Draw circuit diagram from string representation of circuit

        Args:
            string (str): simplified circuit string
            parallel_parts (dict): dictionary of parallel components
            canvas_size (tuple, optional): size of the circuit (i.e. number of components across and number of components wide). Defaults to (0,0).
            pad (int, optional): fixed length for component labels. Defaults to 5.

        Returns:
            str: string drawing of circuit diagram
        """
        drawing = ''

        def trim(d):
            """Trim excess lines from diagram"""
            lines = list(d.split('\n'))
            lines = [line for line in lines if not all([(c==' ' or c=='-') for c in line])]
            d = '\n'.join(lines)
            return d
        
        if canvas_size[0] == 0 and canvas_size[1] == 0:
            canvas_size = self.sizeCircuit(string, parallel_parts)
        components = string.split('-')

        if len(components) == 1:
            component = components[0]

            # Connect components in parallel
            if component.startswith('Pr'):
                subs = parallel_parts[component]
                for sub in subs:
                    d = self.drawCircuit(sub, parallel_parts, pad=pad)
                    drawing = self.mergeCircuit(drawing, d, 'v') if len(drawing) else d
                drawing = trim(drawing)
                return drawing

            # Single component
            else:
                drawing = f"-{component.ljust(pad, '-')}-"
                drawing = trim(drawing)
                return drawing
        
        # Connect components in series
        for component in components:
            if component.startswith('Pr'):
                sep = '-' + canvas_size[1]*'\n '
                drawing = self.mergeCircuit(drawing, sep, 'h')
            d = self.drawCircuit(component, parallel_parts, canvas_size, pad)
            drawing = self.mergeCircuit(drawing, d, 'h') if len(drawing) else d
        drawing = trim(drawing)
        return drawing

    def mergeCircuit(self, this:str, that:str, orientation:str):
        """
        Concatenate circuit component diagrams

        Args:
            this (str): string representation of left circuit diagram
            that (str): string representation of right circuit diagram
            orientation (str): orientation to merge diagrams ("h,H,horizontal" / "v,V,vertical")

        Returns:
            str: merged string drawing of circuit diagram
        """
        merged = ''
        this_lines = list(this.split('\n'))
        that_lines = list(that.split('\n'))
        this_size = (max([len(line) for line in this_lines]), len(this_lines))
        that_size = (max([len(line) for line in that_lines]), len(that_lines))
        if orientation in ['h','H','horizontal']:
            for l in range(max(this_size[1], that_size[1])):
                this_line = this_lines[l] if l<len(this_lines) else this_size[0]*" "
                that_line = that_lines[l] if l<len(that_lines) else that_size[0]*" "
                merged = merged + this_line + that_line + "\n"
        elif orientation in ['v','V','vertical']:
            max_width = max(this_size[0], that_size[0])
            this_lines = [line.ljust(max_width, '-') for line in this_lines]
            that_lines = [line.ljust(max_width, '-') for line in that_lines]
            merged = "\n".join(this_lines) + "\n" + "\n".join(that_lines)
        return merged

    def simplifyCircuit(self, string:str, verbose=True):
        """
        Generate parenthesised contents in string as pairs (level, contents)

        Args:
            string (str): string representation of circuit
            verbose (bool, optional): whether to display outcome. Defaults to True.

        Returns:
            str, dict: string representation of circuit; dictionary of parallel components
        """
        def find_all(a_str, sub):
            start = 0
            while True:
                start = a_str.find(sub, start)
                if start == -1: return
                yield start
                start += len(sub)
        
        parallel_starts = {f'Pr{i+1}': p for i, p in enumerate(list(find_all(string, 'p(')))}
        parallel_parts = {}

        for i in range(len(parallel_starts),0,-1):
            abbr = f'Pr{i}'
            start = parallel_starts[abbr]
            end = string.find(')', start)
            parallel_parts[abbr] = tuple(string[start+2:end].split(','))
            string = string[:start] + abbr + string[end+1:]
        if verbose:
            print(string)
            print(parallel_parts)
        return string, parallel_parts

    def sizeCircuit(self, string:str, parallel_parts:dict):
        """
        Find the size of the circuit (i.e. number of components across and number of components wide)

        Args:
            string (str): simplified circuit string
            parallel_parts (dict): dictionary of parallel components

        Returns:
            tuple: size of circuit
        """
        size = (0,0)
        components = string.split('-')
        if len(components) == 1:
            component = components[0]
            if component.startswith('Pr'):
                subs = parallel_parts[component]
                max_width, max_height = (1, 1)
                for sub in subs:
                    s = self.sizeCircuit(sub, parallel_parts)
                    max_width = max(max_width, s[0])
                    size = (max_width, size[1]+s[1])
                return size
            else:
                size = (1,1)
                return size
        
        max_height = size[1]
        for component in components:
            s = self.sizeCircuit(component, parallel_parts)
            max_height = max(max_height, s[1])
            size = (size[0]+s[0], max_height)
        return size
