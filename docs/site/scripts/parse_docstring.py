# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
import griffe
from typing import Any

class ClassDocstringCleaner(griffe.Extension):
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
            # docstring = docstring.replace("## Attributes", "Attributes")
            # docstring = docstring.replace("### Attributes", "Attributes")
            docstring = docstring.replace("### Methods", "Methods")
            docstring = docstring.replace("## Methods", "Methods")
            docstring = docstring.replace("`", "")
            docstring = docstring.replace("and properties", "")
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
            docstring = docstring.replace("## ", "")
            docstring = docstring.replace("### ", "")
            docstring = docstring.replace("`", "")
            mod.docstring.value = docstring
