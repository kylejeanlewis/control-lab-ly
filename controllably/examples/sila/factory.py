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
    
<i>Documentation last updated: 2025-06-11</i>
"""
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
    
    Args:
        prime (Any): The SiLA2 feature class or instance to generate XML for.
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
        
def write_feature(prime: Any) -> ET.Element:
    """
    Write the XML structure for a SiLA2 feature based on a Python class.
    
    Args:
        prime (Any): The SiLA2 feature class or instance to generate XML for.
        
    Returns:
        ET.Element: The root element of the XML structure for the SiLA2 feature.
    """
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
    description: str = "DESCRIPTION",
    observable: bool = False,
) -> ET.Element:
    """
    Write a property element for a SiLA2 feature.
    
    Args:
        attr_name (str): The name of the property attribute.
        parent (ET.Element): The parent XML element to append the property to.
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
    property_ = write_data_type(property_)
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
