# -*- coding: utf-8 -*-
import sys

destination_folder = sys.argv[1] if len(sys.argv) > 1 else '.'

from . import start_project_here

if __name__ == '__main__':
    start_project_here(destination_folder)
    print(f"Project initialized in {destination_folder}")
