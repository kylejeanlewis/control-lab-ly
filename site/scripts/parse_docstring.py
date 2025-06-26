# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import ast
import re
from typing import Any

# Third-party imports
import griffe


class DocstringCleaner(griffe.Extension):
    """
    A Griffe VisitorExtension to clean ONLY class docstrings
    by removing '### ' and '`' substrings.
    """
    
    def on_class_instance(
        self,
        *,
        node: ast.AST | griffe.ObjectNode,
        cls: griffe.Class,
        agent: griffe.Visitor | griffe.Inspector,
        **kwargs: Any,
    ) -> None:
        if cls.docstring:
            # If the node has a docstring, apply replacements
            docstring = cls.docstring.value
            
            # Remove 'Constructor' section if it exists
            pattern = r"### Constructor.*?### Attributes"
            docstring = re.sub(pattern, "### Attributes", docstring, flags=re.DOTALL)
            
            # Replace specific substrings in the docstring
            docstring = docstring.replace("### Attributes", "Attributes")
            docstring = docstring.replace("## Attributes", "Attributes")
            docstring = docstring.replace(" and properties", "")
            docstring = docstring.replace("### Methods", "Methods")
            docstring = docstring.replace("## Methods", "Methods")
            docstring = docstring.replace("`", "")
            
            # Remove lines containing '####' from the docstring
            lines = docstring.splitlines()
            filtered_lines = [line for line in lines if '####' not in line]
            docstring = "\n".join(filtered_lines)
            
            cls.docstring.value = docstring
        return
            
    def on_module_instance(
        self,
        *,
        node: ast.AST | griffe.ObjectNode,
        mod: griffe.Module,
        agent: griffe.Visitor | griffe.Inspector,
        **kwargs: Any,
    ) -> None:
        try:
            docstring = mod.docstring
        except AttributeError:
            text = mod.__dict__
            raise TypeError(text)
        if mod.docstring:
            # If the node has a docstring, apply replacements
            docstring = mod.docstring.value
            docstring = docstring.replace("### ", "")
            docstring = docstring.replace("## ", "")
            docstring = docstring.replace("`", "")
            mod.docstring.value = docstring
