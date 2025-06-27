# -*- coding: utf-8 -*-
import os
from pathlib import Path
import shutil
import yaml

def remove_folder_if_exists(folder_path):
    """
    Removes a folder and all its contents if it exists.
    Handles cases where the folder is not empty and may or may not exist.

    Args:
        folder_path (str): The path to the folder to be removed.
    """
    if not isinstance(folder_path, (str,Path)):
        print(f"Error: Invalid folder_path type. Expected string, got {type(folder_path)}.")
        return

    print(f"Attempting to remove folder: '{folder_path}'")

    try:
        shutil.rmtree(folder_path)
        print(f"Folder '{folder_path}' and its contents removed successfully.")
    except FileNotFoundError:
        print(f"Folder '{folder_path}' does not exist (or was already removed). No action needed.")
    except OSError as e:
        # Catch other potential OS errors (e.g., permissions issues, folder is a file)
        print(f"Error removing folder '{folder_path}': {e}")
    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred while trying to remove '{folder_path}': {e}")

def get_import_path(py_path, src_dir, import_base="controllably"):
    rel_path = os.path.relpath(py_path, src_dir)
    no_ext = os.path.splitext(rel_path)[0]
    parts = no_ext.split(os.sep)
    return ".".join([import_base] + parts)

def generate_markdown_for_py(py_path, md_path, src_dir, import_base="controllably"):
    filename = os.path.basename(py_path)
    title = os.path.splitext(filename)[0].replace('_', ' ').title()
    import_path = get_import_path(py_path, src_dir, import_base)
    md_content = f"# {title}\n\n::: {import_path}\n"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

def should_exclude(file_path, src_dir):
    # Exclude __init__.py, __main__.py, and anything under an 'external' folder
    filename = os.path.basename(file_path)
    if filename in ('__init__.py', '__main__.py'):
        return True
    rel_path = os.path.relpath(file_path, src_dir)
    parts = rel_path.split(os.sep)
    return 'external' in parts

def crawl_and_generate_markdown(src_dir, dst_dir, import_base="controllably"):
    """
    Crawl src_dir for .py files and generate markdown files in dst_dir, preserving structure,
    excluding __init__.py, __main__.py, and anything under an 'external' folder.
    Also returns a nested dictionary representing the folder structure for YAML nav.
    """
    structure = {}
    for root, dirs, files in os.walk(src_dir):
        # Exclude 'external' folders from traversal
        dirs[:] = [d for d in dirs if d.lower() not in ('external', '__pycache__')]
        rel_dir = os.path.relpath(root, src_dir)
        dst_root = os.path.join(dst_dir, rel_dir)
        os.makedirs(dst_root, exist_ok=True)
        md_files = []
        for file in files:
            if file.endswith('.py'):
                py_path = os.path.join(root, file)
                if should_exclude(py_path, src_dir):
                    continue
                md_name = os.path.splitext(file)[0] + '.md'
                md_path = os.path.join(dst_root, md_name)
                generate_markdown_for_py(py_path, md_path, src_dir, import_base)
                md_files.append((os.path.splitext(file)[0], os.path.relpath(md_path, dst_dir).replace("\\", "/")))
        # Build structure dictionary
        if md_files:
            d = structure
            if rel_dir != ".":
                for part in rel_dir.split(os.sep):
                    d = d.setdefault(part, {})
            for name, rel_md in md_files:
                d[name] = f"site/api/{rel_md}"
    return structure

def structure_to_yaml_dict(structure):
    """
    Convert the nested structure dictionary to a YAML nav list.
    """
    def convert(d):
        nav = []
        for k, v in sorted(d.items()):
            if isinstance(v, dict):
                nav.append({k: convert(v)})
            else:
                nav.append({k: v})
        return nav
    return convert(structure)

def write_yaml_nav(structure, yaml_path):
    """
    Write the nav structure to a YAML file.
    """
    nav = structure_to_yaml_dict(structure)
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(nav, f, sort_keys=False, allow_unicode=True)

def main():
    source_directory = "controllably"
    destination_directory = Path("docs/site/api")
    remove_folder_if_exists(destination_directory)
    yaml_nav_path = os.path.join(destination_directory, "reference_nav.yaml")
    structure = crawl_and_generate_markdown(source_directory, destination_directory, import_base="controllably")
    write_yaml_nav(structure, yaml_nav_path)
    
if __name__ == "__main__":
    main()
