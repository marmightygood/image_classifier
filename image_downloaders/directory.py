"""Directory manager.

Manages directories for storing image files locally

    methods:

    prime (directory_path)
        Creates a new directory, or removes and re-creates an existing one.
"""

import os
import shutil

def prime (directory_path):
    if os.path.exists(directory_path):
        shutil.rmtree(directory_path) 
    os.mkdir (directory_path)    