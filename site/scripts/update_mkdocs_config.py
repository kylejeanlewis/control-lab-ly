# -*- coding: utf-8 -*-
from pathlib import Path
import yaml

def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_yaml(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

def update_reference_nav(mkdocs_path, reference_nav_path):
    mkdocs = load_yaml(mkdocs_path)
    reference_nav = load_yaml(reference_nav_path)

    # Find the 'nav' section and the 'Reference' entry
    nav = mkdocs.get('nav', [])
    for idx, item in enumerate(nav):
        if isinstance(item, dict) and 'Reference' in item:
            nav[idx]['Reference'] = reference_nav
            break
    else:
        # If not found, append it
        nav.append({'Reference': reference_nav})

    mkdocs['nav'] = nav
    save_yaml(mkdocs, mkdocs_path)

def main():
    mkdocs_path = "mkdocs.yaml"
    reference_nav_path = Path("docs/site/api/reference_nav.yaml")
    update_reference_nav(mkdocs_path, reference_nav_path)

if __name__ == "__main__":
    main()
    