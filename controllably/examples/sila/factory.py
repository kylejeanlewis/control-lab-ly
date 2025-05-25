# -*- coding: utf-8 -*-
# Standard library imports
import inspect
import logging
import re
from typing import Callable, Any
import xml.etree.ElementTree as ET

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
    "Any": "Any",
}
BASIC_TYPES = tuple(type_mapping.values())

def create_xml(prime: Any):
    """
    Write the XML data to a file.
    """
    feature = write_feature(prime)
    tree = ET.ElementTree(feature)
    ET.indent(tree, space="  ", level=0) # Using 2 spaces for indentation
    filename = feature.find('Identifier').text
    tree.write(f"{filename}.xml", encoding="utf-8", xml_declaration=True)
    logger.warning(f"XML file '{filename}.xml' generated successfully.\n")
    logger.warning('1) Remove any unnecessary commands and properties.')
    logger.warning('2) Verify the data types, replacing the "Any" fields as needed.')
    logger.warning('3) Fill in the "DESCRIPTION" fields in the XML file.')
    return
        
def write_feature(prime: Any):
    class_name = prime.__name__ if inspect.isclass(prime) else prime.__class__.__name__
    feature = ET.Element("Feature")
    feature = write_header(feature)
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
        feature = write_property(attr_name, feature)
    for attr in commands:
        feature = write_command(attr, feature)
    
    return feature

def write_header(
    parent: ET.Element,
    originator:str = "controllably", 
    category: str = "setup"
):
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

def write_identifier(parent: ET.Element, text:str):
    identifier = ET.SubElement(parent, "Identifier")
    identifier.text = to_pascal_case(text)
    return parent
    
def write_display_name(parent: ET.Element, text:str):
    display_name = ET.SubElement(parent, "DisplayName")
    display_name.text = to_title_case(text)
    return parent
    
def write_description(parent: ET.Element, text:str):
    description = ET.SubElement(parent, "Description")
    description.text = text
    return parent

def write_observable(parent: ET.Element, observable: bool):
    observable_ = ET.SubElement(parent, "Observable")
    observable_.text = 'Yes' if observable else 'No'
    return parent

def write_data_type(
    parent: ET.Element, 
    data_type: str = "Any",
    is_list: bool = False
):
    is_list = is_list or data_type.lower() == "list"
    data_type_ = ET.SubElement(parent, "DataType")
    if is_list:
        list_ = ET.SubElement(data_type_, "List")
        data_type_1 = ET.SubElement(list_, "DataType")
        basic_ = ET.SubElement(data_type_1, "Basic")
        basic_.text = data_type if data_type.lower() != "list" else "Any"
    else:
        basic_ = ET.SubElement(data_type_, "Basic")
        basic_.text = data_type
    return parent

def write_property(
    attr_name: str,
    parent: ET.Element,
    *,
    description: str|None = None,
    observable: bool = False,
):
    property_ = ET.SubElement(parent, "Property")
    property_ = write_identifier(property_, attr_name)
    property_ = write_display_name(property_, attr_name)
    property_ = write_description(property_, description or "DESCRIPTION")
    property_ = write_observable(property_, observable)
    property_ = write_data_type(property_)
    return parent
    
def write_command(
    attr: Callable,
    parent: ET.Element,
    *,
    observable: bool = False,
):
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
            data_type = type_mapping.get(str(param.annotation), "Any")
        command_ = write_parameter(command_, param.name, param.name, data_type)
    command_ = write_response(command_)
    return parent
    
def write_parameter(
    parent: ET.Element,
    identifier: str,
    display_name: str,
    data_type: str,
    *,
    description: str|None = None
):
    parameter_ = ET.SubElement(parent, "Parameter")
    parameter_ = write_identifier(parameter_, identifier)
    parameter_ = write_display_name(parameter_, display_name)
    parameter_ = write_description(parameter_, description or "DESCRIPTION")
    parameter_ = write_data_type(parameter_, data_type)
    return parent
    
def write_response(
    parent: ET.Element,
    identifier: str|None = None,
    display_name: str|None = None,
    data_type: str = "Any",
    *,
    description: str|None = None
):
    response_ = ET.SubElement(parent, "Response")
    response_ = write_identifier(response_, identifier or "Response")
    response_ = write_display_name(response_, display_name or "Response")
    response_ = write_description(response_, description or "DESCRIPTION")
    response_ = write_data_type(response_, data_type)
    return parent
