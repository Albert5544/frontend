# This module gets maps and sets of filenames and filepaths in a directory

from pathlib import Path
from collections import defaultdict
import os

def generate_map(p):
    # p -> Path object of the folder
    arr = {}
    for i in p.rglob('*'):
        arr[i.relative_to('.')] = str(i.resolve()) # map from relative address to absolute address of all files in the directory
    return arr

def directory(dir_name): # Returns a map from relative address to absolute address of all files in the directory
    p = Path('./' + dir_name)
    if(p.is_dir()):
        arr = generate_map(p)
        return arr
    else:
        print("No such directory exists\n")

def generate_multimap(folder_name): # This maps filenames to their absolute path, this is one to many, as there can be same filenames with different paths
    p = Path('./'+folder_name)
    arr = defaultdict(list)
    for i in p.rglob('*'):
        arr[i.name].append(str(i.resolve()))
    return arr

def generate_set(folder_name): # This returns a set all relative address of all python files in the directory
    dir = './'+folder_name
    p = Path(dir)
    arr = set()
    for i in p.rglob('*.py'):
        arr.add(i.relative_to('.'))
    return arr

def generate_modules(folder_name): # This returns a set of all user defined python modules
    dir = './'+folder_name
    p = Path(dir)
    arr = set()
    for i in p.rglob('*.py'):
        arr.add(i.stem)
    return arr

