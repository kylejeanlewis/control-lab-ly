# %% -*- coding: utf-8 -*-
"""
This module holds functions to manipulate circuit diagrams.

Functions:
    draw_circuit
    merge_circuit
    simplify_circuit
    size_circuit
"""
# Standard library imports
from __future__ import annotations

def draw_circuit(
        circuit: str, 
        parallel_parts: dict, 
        canvas_size: tuple[int, int] = (0,0), 
        pad: int = 5
    ) -> str:
    """
    Draw circuit diagram from string representation of circuit

    Args:
        circuit (str): simplified circuit string
        parallel_parts (dict): dictionary of parallel components
        canvas_size (tuple, optional): size of the circuit (i.e. number of components across and number of components wide). Defaults to (0,0).
        pad (int, optional): fixed length for component labels. Defaults to 5.

    Returns:
        str: string drawing of circuit diagram
    """
    drawing = ''

    def trim(diagram:str) -> str:
        """
        Trim excess lines from diagram
        
        Args:
            diagram (str): diagram string
            
        Returns:
            str: trimmed diagram
        """
        lines = list(diagram.split('\n'))
        lines = [line for line in lines if not all([(c==' ' or c=='-') for c in line])]
        diagram = '\n'.join(lines)
        return diagram
    
    if canvas_size[0] == 0 and canvas_size[1] == 0:
        canvas_size = size_circuit(circuit, parallel_parts)
    components = circuit.split('-')

    if len(components) == 1:
        component = components[0]

        # Connect components in parallel
        if component.startswith('Pr'):
            subs = parallel_parts[component]
            for sub in subs:    # recursively draw sub-components, then merging
                d = draw_circuit(sub, parallel_parts, pad=pad)
                drawing = merge_circuit(drawing, d, 'v') if len(drawing) else d
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
            drawing = merge_circuit(drawing, sep, 'h')
        d = draw_circuit(component, parallel_parts, canvas_size, pad)
        drawing = merge_circuit(drawing, d, 'h') if len(drawing) else d
    drawing = trim(drawing)
    return drawing

def merge_circuit(this:str, that:str, orientation:str) -> str:
    """
    Concatenate circuit component diagrams

    Args:
        this (str): string representation of first circuit diagram
        that (str): string representation of second circuit diagram
        orientation (str): orientation to merge diagrams ("h,H,horizontal" / "v,V,vertical")

    Returns:
        str: merged string drawing of circuit diagram
    """
    merged = ''
    this_lines = list(this.split('\n'))
    that_lines = list(that.split('\n'))
    this_size = (max([len(line) for line in this_lines]), len(this_lines))
    that_size = (max([len(line) for line in that_lines]), len(that_lines))
    if orientation.lower()[0] == 'h':
        for l in range(max(this_size[1], that_size[1])):
            this_line = this_lines[l] if l<len(this_lines) else this_size[0]*" "
            that_line = that_lines[l] if l<len(that_lines) else that_size[0]*" "
            merged = merged + this_line + that_line + "\n"
    elif orientation.lower()[0] == 'v':
        max_width = max(this_size[0], that_size[0])
        this_lines = [line.ljust(max_width, '-') for line in this_lines]
        that_lines = [line.ljust(max_width, '-') for line in that_lines]
        merged = "\n".join(this_lines) + "\n" + "\n".join(that_lines)
    return merged

def simplify_circuit(circuit:str, verbose:bool = True) -> tuple[str, dict[str, str]]:
    """
    Generate parenthesised contents in string as pairs (level, contents)

    Args:
        circuit (str): string representation of circuit
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
    
    parallel_starts = {f'Pr{i+1}': p for i, p in enumerate(list(find_all(circuit, 'p(')))}
    parallel_parts = {}

    for i in range(len(parallel_starts),0,-1):
        abbr = f'Pr{i}'
        start = parallel_starts[abbr]
        end = circuit.find(')', start)
        parallel_parts[abbr] = tuple(circuit[start+2:end].split(','))
        circuit = circuit[:start] + abbr + circuit[end+1:]
    if verbose:
        print(circuit)
        print(parallel_parts)
    return circuit, parallel_parts

def size_circuit(circuit:str, parallel_parts:dict) -> tuple[int, int]:
    """
    Find the size of the circuit (i.e. number of components across and number of components wide)

    Args:
        circuit (str): simplified circuit string
        parallel_parts (dict): dictionary of parallel components

    Returns:
        tuple: size of circuit
    """
    size = (0,0)
    components = circuit.split('-')
    if len(components) == 1:
        component = components[0]
        if component.startswith('Pr'):
            subs = parallel_parts[component]
            max_width, max_height = (1, 1)
            for sub in subs:    # recursively find the size of parallel components
                s = size_circuit(sub, parallel_parts)
                max_width = max(max_width, s[0])
                size = (max_width, size[1]+s[1])
            return size
        else:
            size = (1,1)
            return size
    
    max_height = size[1]
    for component in components:
        s = size_circuit(component, parallel_parts)
        max_height = max(max_height, s[1])
        size = (size[0]+s[0], max_height)
    return size


class CircuitDiagram(object):
    """
    Circuit diagram manipulator.
    """
    def __init__(self):
        return

    @classmethod
    def drawCircuit(cls, string:str, parallel_parts:dict, canvas_size=(0,0), pad=5):
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
            canvas_size = cls.sizeCircuit(string, parallel_parts)
        components = string.split('-')

        if len(components) == 1:
            component = components[0]

            # Connect components in parallel
            if component.startswith('Pr'):
                subs = parallel_parts[component]
                for sub in subs:
                    d = cls.drawCircuit(sub, parallel_parts, pad=pad)
                    drawing = cls.mergeCircuit(drawing, d, 'v') if len(drawing) else d
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
                drawing = cls.mergeCircuit(drawing, sep, 'h')
            d = cls.drawCircuit(component, parallel_parts, canvas_size, pad)
            drawing = cls.mergeCircuit(drawing, d, 'h') if len(drawing) else d
        drawing = trim(drawing)
        return drawing

    @staticmethod
    def mergeCircuit(this:str, that:str, orientation:str):
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

    @staticmethod
    def simplifyCircuit(string:str, verbose=True):
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

    @classmethod
    def sizeCircuit(cls, string:str, parallel_parts:dict):
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
                    s = cls.sizeCircuit(sub, parallel_parts)
                    max_width = max(max_width, s[0])
                    size = (max_width, size[1]+s[1])
                return size
            else:
                size = (1,1)
                return size
        
        max_height = size[1]
        for component in components:
            s = cls.sizeCircuit(component, parallel_parts)
            max_height = max(max_height, s[1])
            size = (size[0]+s[0], max_height)
        return size
