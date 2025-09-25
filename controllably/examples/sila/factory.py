# -*- coding: utf-8 -*-
""" 
This module provides functions to generate XML files for SiLA2 features based on Python classes.
It includes functions to write feature headers, identifiers, display names, descriptions, properties, and commands.
It also includes utility functions to convert naming conventions and handle data types.
This is useful for creating SiLA2-compliant XML files that describe the features of a device or service.

It is designed to be used with Python classes that represent SiLA2 features, allowing for easy generation of XML files that can be used in SiLA2 applications.

Attributes:
    type_mapping (dict): A mapping of Python types to SiLA2 data types.
    BASIC_TYPES (tuple): A tuple of basic SiLA2 data types.
    
## Functions:
    `create_setup_sila_package`: Generates a SiLA2 package from a setup class, creating XML files and modifying server and implementation code.
    `create_xml`: Generates an XML file for the given SiLA2 feature class.
    `write_feature`: Writes the XML structure for a SiLA2 feature based on a Python class.
    `write_header`: Writes the header information for the SiLA2 feature XML.
    `split_by_words`: Splits a string into words based on common naming conventions.
    `to_pascal_case`: Converts a string to PascalCase.
    `to_title_case`: Converts a string to Title Case.
    `write_identifier`: Writes the identifier element for a SiLA2 feature.
    `write_display_name`: Writes the display name element for a SiLA2 feature.
    `write_description`: Writes the description element for a SiLA2 feature.
    `write_observable`: Writes the observable element for a SiLA2 feature.
    `write_data_type`: Writes the data type element for a SiLA2 feature.
    `write_property`: Writes a property element for a SiLA2 feature.
    `write_command`: Writes a command element for a SiLA2 feature.
    `write_parameter`: Writes a parameter element for a SiLA2 command.
    `write_response`: Writes a response element for a SiLA2 command.
    `resolve_annotation_type`: Resolves the type of a SiLA2 feature based on its annotations.
    
<i>Documentation last updated: 2025-06-11</i>
"""
# Standard library imports
import inspect
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Callable, Any, Sequence
import xml.etree.ElementTree as ET

# Local application imports
from .modifier import modify_server_file, modify_generated_file, copy_from_existing

logger = logging.getLogger(__name__)

type_mapping = {
    "str": "String",
    "int": "Integer",
    "float": "Real",
    "bool": "Boolean",
    "bytes": "Binary",
    "datetime.date": "Date",
    "datetime.time": "Time",
    "datetime.datetime": "Timestamp",
    "list": "List",
    "tuple": "List",
    "set": "List",
    "Sequence": "List",
    "np.ndarray": "List",  # Assuming numpy arrays are treated as lists
    "Any": "Any",
}
LIST_LIKE = ("list", "tuple", "set", "Sequence", "np.ndarray")
BASIC_TYPES = tuple(type_mapping.values())

def create_setup_sila_package(
    setup: Any, 
    setup_name: str, 
    dst_folder: Path|str,
    library:Path|str|None = None,
    skip_checks: bool = False
):
    """
    Generate a SiLA2 package from a setup class, creating XML files and modifying server and implementation code.
    
    Args:
        setup (Any): The setup class or instance to generate the SiLA2 package from.
        setup_name (str): The name of the setup, used for naming the generated package.
        dst_folder (Path|str): The destination folder where the SiLA2 package will be created.
        library (Path|str|None): Optional path to an existing library to copy XML and implementation files from.
        skip_checks (bool): If True, skips checks for 'Any' data types and unimplemented methods.
    """
    dst_folder = Path(dst_folder)
    output_directory = dst_folder/setup_name
    
    # 1. Create SiLA xml files
    xml_paths: dict[tuple[str,str], Path] = {}
    impl_paths: dict[tuple[str,str], Path] = {}
    for name, value in setup.__dict__.items():
        xml_path = create_xml(value, output_directory/'xml')
        class_name: str = value.__class__.__name__
        class_name = to_pascal_case(class_name)
        xml_paths[(class_name,name)] = xml_path
        impl_paths[(class_name,name)] = output_directory/f'{setup_name}_sila'/'feature_implementations'/f'{class_name.lower()}_impl.py'
    
    # 1a. Copy existing library xml files if provided
    if library:
        for xml_path in xml_paths.values():
            copy_from_existing(xml_path, library)  # Copy from existing library if available
    
    # 1b. Ensure all Any data types are replaced appropriately
    any_text = "<Basic>Any</Basic>"
    xml_paths_with_any = [xml_path for xml_path in xml_paths.values() if any_text in xml_path.read_text()]
    input_any = "skip" if skip_checks else ""
    while len(xml_paths_with_any):
        if skip_checks or input_any.strip().lower() == 'skip':
            break
        logger.warning('\n'.join(list(map(str,xml_paths_with_any))))
        logger.warning('\n')
        time.sleep(0.1)
        input_any = input("Some XML files still contain 'Any' data types. Replace with appropriate types or type 'skip' to ignore.")
        xml_paths_with_any = [xml_path for xml_path in xml_paths.values() if any_text in xml_path.read_text()]
    
    # 2. Generate Sila2 package
    result = subprocess.run([
        'sila2-codegen', 
        'new-package',
        '--package-name', f'{setup_name}_sila',
        '--output-directory', str(output_directory),
        *[str(path) for path in xml_paths.values()]
    ], check=True, capture_output=True, text=True)
    if result.stderr:
        for line in result.stderr.splitlines():
            logger.error(line)
        raise RuntimeError(f"Failed to generate SiLA2 package: {result.stderr}")
    logger.warning(f"'{setup_name}_sila' package generated successfully in {output_directory}.")
    
    # 3. Modify Server and Implementation code
    modify_server_file(output_directory/f'{setup_name}_sila'/'server.py', setup_name=setup_name)
    for (class_name, object_name), impl_path in impl_paths.items():
        modify_generated_file(impl_path, class_name, object_name, setup_name=setup_name)

    # 3a. Copy existing library implementation files if provided
    if library:
        for impl_path in impl_paths.values():
            copy_from_existing(impl_path, library)  # Copy from existing library if available
    
    # 3b. Check if any methods are not implemented
    not_implemented_text = "raise NotImplementedError  # TODO"
    impl_paths_with_not_implemented = [impl_path for impl_path in impl_paths.values() if not_implemented_text in impl_path.read_text()]
    input_impl = "skip" if skip_checks else ""
    while len(impl_paths_with_not_implemented):
        if skip_checks or input_impl.strip().lower() == 'skip':
            break
        logger.warning('\n'.join(list(map(str,impl_paths_with_not_implemented))))
        logger.warning('\n')
        time.sleep(0.1)
        input_impl = input("Some implementation files still contain 'NotImplementedError'. Implement them or type 'skip' to ignore.")
        impl_paths_with_not_implemented = [impl_path for impl_path in impl_paths.values() if not_implemented_text in impl_path.read_text()]
    
    # 4. Install newly generated Sila2 package
    result = subprocess.run([
        sys.executable, '-m',
        'pip', 'install', '-e',
        str(output_directory),
        '--config-settings', 'editable_mode=strict'
    ], check=True, capture_output=True, text=True)
    if result.stderr:
        error_flag = False
        pip_dependency_notice = (
            '[notice] A new release of pip is available:',
            '[notice] To update, run: python.exe -m pip install --upgrade pip'
        )
        for line in result.stderr.splitlines():
            logger.error(line)
            if line and not line.startswith(pip_dependency_notice):
                error_flag = True
        if error_flag:
            raise RuntimeError(f"Failed to install SiLA2 package: {result.stderr}")
    logger.warning(f"'{setup_name}_sila' package installed successfully.")
    return

def create_xml(prime: Any, directory: str = ".") -> Path:
    """
    Write the XML data to a file.
    
    Args:
        prime (Any): The SiLA2 feature class or instance to generate XML for.
        directory (str): The directory where the XML file will be saved. Defaults to the current directory.
    
    Returns:
        Path: The path to the generated XML file.
    """
    feature = write_feature(prime)
    tree = ET.ElementTree(feature)
    ET.indent(tree, space="  ", level=0) # Using 2 spaces for indentation
    class_name = feature.find('Identifier').text
    filepath = Path(directory)/f"{class_name}.sila.xml"
    os.makedirs(filepath.parent, exist_ok=True)  # Ensure the directory exists
    tree.write(filepath, encoding="utf-8", xml_declaration=True)
    logger.warning(f"\n'{class_name}.sila.xml' generated successfully.")
    logger.warning('1) Remove any unnecessary commands and properties.')
    logger.warning('2) Verify the data types, replacing the "Any" fields as needed.')
    logger.warning('3) Fill in the "DESCRIPTION" fields in the XML file.\n')
    return filepath
        
def write_feature(prime: Any) -> ET.Element:
    """
    Write the XML structure for a SiLA2 feature based on a Python class.
    
    Args:
        prime (Any): The SiLA2 feature class or instance to generate XML for.
        
    Returns:
        ET.Element: The root element of the XML structure for the SiLA2 feature.
    """
    class_name = prime.__name__ if inspect.isclass(prime) else prime.__class__.__name__
    module_name = prime.__module__ if inspect.isclass(prime) else prime.__class__.__module__
    feature = ET.Element("Feature")
    originator = module_name.split('.')[0] if '.' in module_name else module_name
    try:
        category = [m for m in module_name.split('.') if m[0].isupper()][0]
    except IndexError:
        idx = 1 if len(module_name.split('.')) > 1 else -1
        category = module_name.split('.')[idx]
    category = to_pascal_case(category)
    feature = write_header(feature, originator=originator, category=category.lower())
    feature = write_identifier(feature, class_name)
    feature = write_display_name(feature, class_name)
    feature = write_description(feature, prime.__doc__)
    
    properties = []
    commands = []
    for attr_name in dir(prime):
        if attr_name.startswith("_"):
            continue
        attr = getattr(prime, attr_name)
        if callable(attr):
            commands.append(attr)
        else:
            properties.append(attr_name)
    
    for attr_name in properties:
        attr_type = type(getattr(prime, attr_name))
        data_type = type_mapping.get(attr_type.__name__, "Any")
        feature = write_property(attr_name, feature, data_type=data_type)
    for attr in commands:
        feature = write_command(attr, feature)
    
    return feature

def write_header(
    parent: ET.Element,
    originator:str = "controllably", 
    category: str = "setup"
) -> ET.Element:
    """
    Write the header information for the SiLA2 feature XML.
    
    Args:
        parent (ET.Element): The parent XML element to append the header to.
        originator (str): The originator of the SiLA2 feature.
        category (str): The category of the SiLA2 feature.
        
    Returns:
        ET.Element: The parent element with the header information added.
    """
    parent.set('SiLA2Version','1.0')
    parent.set('FeatureVersion','1.0')
    parent.set('MaturityLevel','Verified')
    parent.set('Originator',originator)
    parent.set('Category',category)
    parent.set('xmlns',"http://www.sila-standard.org")
    parent.set('xmlns:xsi',"http://www.w3.org/2001/XMLSchema-instance")
    parent.set('xsi:schemaLocation',"http://www.sila-standard.org https://gitlab.com/SiLA2/sila_base/raw/master/schema/FeatureDefinition.xsd")
    return parent

def split_by_words(name_string: str) -> list[str]:
    """
    Splits a string into words based on common naming conventions (camelCase, snake_case, PascalCase, kebab-case).

    Args:
        name_string (str): The input string in any common naming convention.

    Returns:
        list[str]: A list of words extracted from the input string.
    """
    if not name_string:
        return []

    # Step 1: Replace common delimiters with spaces
    # Handles snake_case, kebab-case, and converts them to space-separated words
    s = name_string.replace('_', ' ').replace('-', ' ')

    # Step 2: Insert spaces before capital letters in camelCase/PascalCase
    # This regex looks for a lowercase letter followed by an uppercase letter,
    # and inserts a space between them.
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', s)
    s = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', s) # Handles acronyms like HTTPRequest -> HTTP Request

    return s.split()

def to_pascal_case(name_string: str) -> str:
    """
    Converts various naming conventions (camelCase, snake_case, PascalCase, kebab-case)
    to PascalCase (e.g., "MyClassName").

    Args:
        name_string (str): The input string in any common naming convention.

    Returns:
        str: The converted string in PascalCase.
    """
    if not name_string:
        return ""

    # Step 3: Split the string into words, capitalize each, and join without spaces
    # Remove any extra spaces that might have been introduced before splitting
    words = [word.capitalize() for word in split_by_words(name_string)]
    return ''.join(words)

def to_title_case(name_string: str) -> str:
    """
    Converts various naming conventions (camelCase, snake_case, PascalCase, kebab-case)
    to Title Case (e.g., "My Awesome Variable").

    Args:
        name_string (str): The input string in any common naming convention.

    Returns:
        str: The converted string in Title Case.
    """
    if not name_string:
        return ""
    
    # Step 3: Capitalize the first letter of each word and ensure the rest are lowercase
    # Then remove any extra spaces that might have been introduced
    return ' '.join(word.capitalize() for word in split_by_words(name_string)).strip()

def write_identifier(parent: ET.Element, text:str) -> ET.Element:
    """
    Write the identifier element for a SiLA2 feature.
    
    Args:
        parent (ET.Element): The parent XML element to append the identifier to.
        text (str): The identifier text to be converted to PascalCase.
        
    Returns:
        ET.Element: The parent element with the identifier added.
    """
    identifier = ET.SubElement(parent, "Identifier")
    identifier.text = to_pascal_case(text)
    return parent
    
def write_display_name(parent: ET.Element, text:str) -> ET.Element:
    """
    Write the display name element for a SiLA2 feature.
    
    Args:
        parent (ET.Element): The parent XML element to append the display name to.
        text (str): The display name text to be converted to Title Case.
        
    Returns:
        ET.Element: The parent element with the display name added.
    """
    display_name = ET.SubElement(parent, "DisplayName")
    display_name.text = to_title_case(text)
    return parent
    
def write_description(parent: ET.Element, text:str) -> ET.Element:
    """
    Write the description element for a SiLA2 feature.
    
    Args:
        parent (ET.Element): The parent XML element to append the description to.
        text (str): The description text.
        
    Returns:
        ET.Element: The parent element with the description added.
    """
    description = ET.SubElement(parent, "Description")
    description.text = text
    return parent

def write_observable(parent: ET.Element, observable: bool) -> ET.Element:
    """
    Write the observable element for a SiLA2 feature.
    
    Args:
        parent (ET.Element): The parent XML element to append the observable to.
        observable (bool): Whether the feature is observable or not.
        
    Returns:
        ET.Element: The parent element with the observable added.
    """
    observable_ = ET.SubElement(parent, "Observable")
    observable_.text = 'Yes' if observable else 'No'
    return parent

def write_data_type(
    parent: ET.Element, 
    data_type: str = "Any",
    is_list: bool = False
) -> ET.Element:
    """
    Write the data type element for a SiLA2 feature.
    
    Args:
        parent (ET.Element): The parent XML element to append the data type to.
        data_type (str): The data type text, defaults to "Any".
        is_list (bool): Whether the data type is a list or not.
        
    Returns:
        ET.Element: The parent element with the data type added.
    """
    is_list = is_list or data_type.startswith("List")
    data_type_ = ET.SubElement(parent, "DataType")
    if is_list:
        list_ = ET.SubElement(data_type_, "List")
        inner_data_type = data_type[5:-1] if data_type.startswith("List[") else "Any"
        list_ = write_data_type(list_, inner_data_type)
    else:
        basic_ = ET.SubElement(data_type_, "Basic")
        basic_.text = data_type
    return parent

def write_property(
    attr_name: str,
    parent: ET.Element,
    data_type: str = "Any",
    *,
    description: str = "DESCRIPTION",
    observable: bool = False,
) -> ET.Element:
    """
    Write a property element for a SiLA2 feature.
    
    Args:
        attr_name (str): The name of the property attribute.
        parent (ET.Element): The parent XML element to append the property to.
        data_type (str, optional): The data type of the property. Defaults to "Any".
        description (str, optional): The description of the property. Defaults to "DESCRIPTION".
        observable (bool, optional): Whether the property is observable or not. Defaults to False.
        
    Returns:
        ET.Element: The parent element with the property added.
    """
    property_ = ET.SubElement(parent, "Property")
    property_ = write_identifier(property_, attr_name)
    property_ = write_display_name(property_, attr_name)
    property_ = write_description(property_, description or "DESCRIPTION")
    property_ = write_observable(property_, observable)
    property_ = write_data_type(property_, data_type)
    return parent
    
def write_command(
    attr: Callable,
    parent: ET.Element,
    *,
    observable: bool = False,
) -> ET.Element:
    """
    Write a command element for a SiLA2 feature.
    
    Args:
        attr (Callable): The command attribute, typically a method of the feature class.
        parent (ET.Element): The parent XML element to append the command to.
        observable (bool, optional): Whether the command is observable or not. Defaults to False.
    
    Returns:
        ET.Element: The parent element with the command added.
    """
    command_ = ET.SubElement(parent, "Command")
    command_ = write_identifier(command_, attr.__name__)
    command_ = write_display_name(command_, attr.__name__)
    command_ = write_description(command_, attr.__doc__ or "DESCRIPTION")
    command_ = write_observable(command_, observable)
    signature = inspect.signature(attr)
    for param in signature.parameters.values():
        if param.name == "self":
            continue
        if param.annotation is inspect.Parameter.empty:
            data_type = "Any"
        else:
            annotated_types = [pa.strip() for pa in str(param.annotation).split('|')]
            data_type = resolve_annotation_type(annotated_types)
        command_ = write_parameter(command_, param.name, param.name, data_type)
    
    if signature.return_annotation is not inspect.Parameter.empty:
        return_types = [rt.strip() for rt in str(signature.return_annotation).split('|')]
        return_data_type = resolve_annotation_type(return_types)
        command_ = write_response(command_, data_type=return_data_type)
    return parent
    
def write_parameter(
    parent: ET.Element,
    identifier: str,
    display_name: str,
    data_type: str,
    *,
    description: str = "DESCRIPTION"
) -> ET.Element:
    """
    Write a parameter element for a SiLA2 command.
    
    Args:
        parent (ET.Element): The parent XML element to append the parameter to.
        identifier (str): The identifier of the parameter.
        display_name (str): The display name of the parameter.
        data_type (str): The data type of the parameter.
        description (str, optional): The description of the parameter. Defaults to "DESCRIPTION".
        
    Returns:
        ET.Element: The parent element with the parameter added.
    """
    parameter_ = ET.SubElement(parent, "Parameter")
    parameter_ = write_identifier(parameter_, identifier)
    parameter_ = write_display_name(parameter_, display_name)
    parameter_ = write_description(parameter_, description or "DESCRIPTION")
    parameter_ = write_data_type(parameter_, data_type)
    return parent
    
def write_response(
    parent: ET.Element,
    identifier: str = "Response",
    display_name: str = "Response",
    data_type: str = "Any",
    *,
    description: str = "DESCRIPTION"
) -> ET.Element:
    """
    Write a response element for a SiLA2 command.
    
    Args:
        parent (ET.Element): The parent XML element to append the response to.
        identifier (str, optional): The identifier of the response. Defaults to "Response".
        display_name (str, optional): The display name of the response. Defaults to "Response".
        data_type (str, optional): The data type of the response. Defaults to "Any".
        description (str, optional): The description of the response. Defaults to "DESCRIPTION".
        
    Returns:
        ET.Element: The parent element with the response added.
    """
    response_ = ET.SubElement(parent, "Response")
    response_ = write_identifier(response_, identifier or "Response")
    response_ = write_display_name(response_, display_name or "Response")
    response_ = write_description(response_, description or "DESCRIPTION")
    response_ = write_data_type(response_, data_type)
    return parent

def resolve_annotation_type(annotations: Sequence[str]) -> str:
    """ 
    Resolves the type of a SiLA2 feature based on its annotations.
    
    Args:
        annotations (Sequence[str]): A sequence of annotations that describe the type.
        
    Returns:
        str: The resolved type of the SiLA2 feature.
    """
    candidate_types = []
    for annotation in annotations:
        if annotation in type_mapping:
            candidate_types.append(type_mapping[annotation])
        elif annotation.startswith(LIST_LIKE):
            if "[" not in annotation:
                return "List"
            inner_annotation = annotation[:-1].split('[',1)[1]
            inner_type = resolve_annotation_type([inner_annotation])
            return f"List[{inner_type}]"
        else:
            candidate_types.append("Any")
    candidate_types = list(set(candidate_types))  # Remove duplicates
    if 'Integer' in candidate_types and 'Real' in candidate_types:
        candidate_types.remove('Integer')
    return candidate_types[0]
