# -*- coding: utf-8 -*-
import sys

from . import start_project_here

if __name__ == '__main__':
    destination_folder = sys.argv[1] if len(sys.argv) > 1 else '.'
    start_project_here(destination_folder)
    print(f"Project initialized in {destination_folder}")
