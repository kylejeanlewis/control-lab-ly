# -*- coding: utf-8 -*-
""" 
This module provides functionality to modify generated SiLA2 server implementation files.
It transforms method bodies that raise NotImplementedError into calls to corresponding methods
on an 'original_object' attribute, and ensures that the server implementation file is correctly set up.

## Classes:
    `ImplementationTransformer`: An AST transformer that modifies method bodies in a specific class.
    
## Functions:
    `copy_from_existing`: Copies the content from an existing SiLA2 implementation or XML file to a new file.
    `modify_generated_file`: Modifies the specified Python template file to replace NotImplementedError calls.
    `modify_server_file`: Modifies the SiLA2 server implementation file to set the name, description, and server type.
"""
# Standard library imports
import ast
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ImplementationTransformer(ast.NodeTransformer):
    """
    Transforms method bodies in a specific class that only raise NotImplementedError
    into calls to a corresponding method on an 'original_object' attribute.
    """
    def __init__(self, target_class_name: str, object_name: str, setup_name:str):
        self.target_class_name = target_class_name
        self.object_name = object_name
        self.setup_name = setup_name
        self.class_node = None
        return
        
    def visit_Module(self, node: ast.Module):
        after_type_check = False
        tool_imported = False
        for stmt in node.body:
            if isinstance(stmt, ast.If) and stmt.test and isinstance(stmt.test, ast.Name) and stmt.test.id == 'TYPE_CHECKING':
                after_type_check = True
                continue
            if not after_type_check:
                continue
            if isinstance(stmt, ast.ImportFrom) and stmt.module == 'tools' and any(alias.name == self.setup_name for alias in stmt.names):
                tool_imported = True
                break
        if not tool_imported:
            import_from_tools = ast.ImportFrom(module='tools', names=[ast.alias(self.setup_name)], level=0)
            node.body.insert(-1, import_from_tools)
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Visit ClassDef nodes. If it's our target class, set a flag so we know
        to process its methods.
        """
        if node.name == self.target_class_name + 'Impl':
            self.class_node = node
            method_names = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            if 'start' not in method_names:
                node.body.insert(1, self._create_start_method())
            if 'stop' not in method_names:
                node.body.insert(2, self._create_stop_method())
            
        # Traverse children
        self.generic_visit(node)
        self.class_node = None # Reset after visiting the class
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """
        Visit FunctionDef nodes (methods). If we're inside the target class
        and the method raises NotImplementedError, replace its body.
        """
        if not isinstance(self.class_node, ast.ClassDef):
            return node
        
        if not self._is_not_implemented_error(node.body):
            return node
        
        is_property = node.name.startswith('get_')
        attr_name = node.name[4:] if is_property else node.name
        attr_name = self._convert_pascal_to_snake(attr_name) if is_property else self._convert_pascal_to_camel(attr_name)
        
        object_attribute = ast.Attribute(
            value=ast.Attribute(
                value=ast.Name(id='self', ctx=ast.Load()),
                attr=self.target_class_name.lower(), ctx=ast.Load()
            ), attr=attr_name, ctx=ast.Load()
        )
        
        if is_property:
            node.body = node.body + [
                ast.Return(value=object_attribute)
            ]
        else:
            keywords = []
            for arg in node.args.args:
                if arg.arg in ('self',):
                    continue
                kw = self._convert_pascal_to_snake(arg.arg)
                keywords.append(ast.keyword(arg=kw, value=ast.Name(id=arg.arg, ctx=ast.Load())))
            if node.args.kwonlyargs:
                for kw in node.args.kwonlyargs:
                    if kw.arg in ('self','metadata'):
                        continue
                    keywords.append(ast.keyword(arg=kw.arg, value=ast.Name(id=kw.arg, ctx=ast.Load())))
            node.body = node.body + [
                ast.Return(value=ast.Call(
                    func=object_attribute,
                    args=[],
                    keywords=keywords,
                    # args=[ast.Name(id=arg.arg, ctx=ast.Load()) for arg in node.args.args if arg.arg != 'self'],
                    # keywords=[ast.keyword(arg=kw.arg, value=ast.Name(id=kw.arg, ctx=ast.Load())) for kw in node.args.kwonlyargs if kw.arg not in ('self','metadata')] if node.args.kwonlyargs else []
                ))
            ]
        
        self.generic_visit(node) # Continue traversing children of the function (though we replaced its body)
        return node

    def _convert_pascal_to_camel(self, name: str) -> str:
        """
        Converts a PascalCase name to camelCase.
        """
        return name[0].lower() + name[1:] if name else name
    
    def _convert_pascal_to_snake(self, name: str) -> str:
        """
        Converts a PascalCase name to snake_case.
        """
        return ''.join(['_' + c.lower() if c.isupper() else c for c in name]).lstrip('_')
    
    def _create_start_method(self) -> ast.FunctionDef:
        self_start = ast.FunctionDef(
            name='start',
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg='self')],
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[]
            ),
            body=[
                ast.AnnAssign(
                    target=ast.Attribute(
                        value=ast.Name(id='self', ctx=ast.Store()), 
                        attr=self.target_class_name.lower(), ctx=ast.Store()
                    ),
                    annotation=ast.Attribute(
                        value=ast.Name(id=self.setup_name, ctx=ast.Load()), 
                        attr=self.target_class_name, ctx=ast.Load()
                    ),
                    value=ast.Attribute(value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=self.setup_name, ctx=ast.Load()), 
                            attr='setup', ctx=ast.Load()
                        ),
                        args=[],keywords=[]
                    ), attr=self.object_name, ctx=ast.Load()),
                    simple=0
                ),
                ast.Expr(value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Attribute(
                            value=ast.Name(id='self', ctx=ast.Load()), 
                            attr=self.target_class_name.lower(), ctx=ast.Load()
                        ), attr='connect', ctx=ast.Load()
                    ),
                    args=[],keywords=[]
                )),
                ast.Expr(value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Call(
                            func=ast.Name(id='super', ctx=ast.Load()),
                            args=[], keywords=[]
                        ), attr='start', ctx=ast.Load()
                    ),
                    args=[], keywords=[]
                )),
            ],
            decorator_list=[],
            returns=ast.Name(id='None', ctx=ast.Load()),
            type_comment=None,
            type_params=[]
        )
        return self_start
        
    def _create_stop_method(self) -> ast.FunctionDef:
        self_stop = ast.FunctionDef(
            name='stop',
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg='self')],
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[]
            ),
            body=[
                ast.Expr(value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Attribute(
                            value=ast.Name(id='self', ctx=ast.Load()), 
                            attr=self.target_class_name.lower(), ctx=ast.Load()
                        ), attr='disconnect', ctx=ast.Load()
                    ),
                    args=[],keywords=[]
                )),
                ast.Expr(value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Call(
                            func=ast.Name(id='super', ctx=ast.Load()),
                            args=[], keywords=[]
                        ), attr='stop', ctx=ast.Load()
                    ),
                    args=[], keywords=[]
                )),
            ],
            decorator_list=[],
            returns=ast.Name(id='None', ctx=ast.Load()),
            type_comment=None,
            type_params=[]
        )
        return self_stop
    
    def _is_not_implemented_error(self, body_nodes: list[ast.stmt]) -> bool:
        """
        Checks if the method body consists of a single statement that raises NotImplementedError.
        """
        if len(body_nodes) == 1 and isinstance(body_nodes[0], ast.Raise):
            raise_node = body_nodes[0]
            if isinstance(raise_node.exc, ast.Name) and raise_node.exc.id == 'NotImplementedError':
                return True
        return False
    

def copy_from_existing(
    filepath: Path|str, 
    library: Path|str
) -> None:
    """
    Copies the content from an existing SiLA2 implementation or XML file to a new file.
    
    Args:
        filepath (Path|str): Path to the file where content should be copied.
        library (Path|str): Path to the library directory containing existing SiLA2 files.
    """
    filepath = Path(filepath)
    library = Path(library)
    
    if not library.exists():
        logger.error(f"Provided library path '{library}' does not exist.")
        return
    if not filepath.is_file():
        logger.error(f"Provided path '{filepath}' is not a file.")
        return
    
    found_paths = []
    for file_path in library.rglob(filepath.name):
        if file_path.is_file(): # Ensure it's a file, not a directory
            found_paths.append(file_path)
    if len(found_paths) == 1:
        logger.info("Copying content from existing SiLA2 file.")
        filepath.write_text(found_paths[0].read_text())  # Copy content from library
    return

def modify_generated_file(
    generated_filepath: Path, 
    target_class_name: str, 
    object_name: str, 
    setup_name:str
) -> str:
    """
    Modifies the specified Python template file to replace NotImplementedError
    calls with actual method calls to an original object.
    
    Args:
        generated_filepath (Path): Path to the generated Python file.
        target_class_name (str): Name of the class to modify.
        object_name (str): Name of the object to call methods on.
        setup_name (str): Name of the setup for which this modification is being done.
        
    Returns:
        str: The modified code as a string.
    """
    try:
        source_code = generated_filepath.read_text()
        template_filepath = generated_filepath.parent/f'template_{generated_filepath.name}'
        tree = ast.parse(source_code)

        transformer = ImplementationTransformer(target_class_name, object_name, setup_name=setup_name)
        new_tree = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)
        
        modified_code = ast.unparse(new_tree)
        pivot = "if TYPE_CHECKING:"
        new_code = pivot.join([source_code.split(pivot,1)[0], modified_code.split(pivot,1)[1]])
        new_code = new_code.replace("raise NotImplementedError", "raise NotImplementedError  # TODO")
        generated_filepath.write_text(new_code)
        template_filepath.write_text(source_code)  # Save the original template file
        logger.warning(f"\n'{generated_filepath.name}' modified successfully.")
        logger.warning('1) Check the types of inputs and outputs.')
        logger.warning('2) Remove the NotImplementedError after verifying implementation.\n')

    except FileNotFoundError:
        logger.error(f"Error: Generated file '{generated_filepath}' not found.")
    except Exception as e:
        logger.warning(f"An error occurred: {e}")
    return    

def modify_server_file(server_filepath: Path|str, setup_name: str):
    """
    Modifies the SiLA2 server implementation file to set the name, description, and server type.
    
    Args:
        server_filepath (Path|str): Path to the SiLA2 server implementation file.
        setup_name (str): Name of the setup for which this modification is being done.
    """
    server_impl = Path(server_filepath)
    server_code = server_impl.read_text()
    server_code = server_code.replace('name = "TODO"', f'name = "{setup_name.upper()}"')
    server_code = server_code.replace('description = "TODO"', f'description = "SiLA2 server for {setup_name.title()} setup"')
    server_code = server_code.replace('server_type="TODO"', 'server_type="Hardware"')
    server_impl.write_text(server_code)
    return
