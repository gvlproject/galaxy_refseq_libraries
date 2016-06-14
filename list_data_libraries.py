'''
Script to make data library for genus from RefSeq fna files
 usage: list_data_libraries.py [-h] [-d DIR] [-k KEY] [-v] genus

 Add RefSeq reference genomes to galaxy data libraries.

 positional arguments:
   genus              the genus to create a library for

 optional arguments:
   -h, --help         show this help message and exit
   -d DIR, --dir DIR  the RefSeq directory containing all species (overrides
                      default)
   -k KEY, --key KEY  the Galaxy API key to use (overrides default)
   -v, --verbose      Print out debugging information

 Assumes Galaxy instance exists at localhost and refseq folder has the following structure:
    refseq_folder/
        species/
            fna files

'''

from __future__ import print_function
from collections import defaultdict
from bioblend.galaxy import GalaxyInstance

import os
import sys
import argparse


def printerr(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def getFilesInFolder(contents, folder):
    file_names = []
    for item in contents:
        filepath = item['name'].split('/')
        if item['type'] == 'file' and filepath[1] == folder:
            file_names.append(filepath[2])
    return file_names

GALAXY_URL = 'http://127.0.0.1/galaxy/'
GALAXY_KEY = '76822b3132377362e5607732b2574766'
REFSEQ_DIR = '/mnt/galaxyIndices/Bacteria/'

# Get things like API Key, RefSeq directory and genus from command line
parser = argparse.ArgumentParser(description='Add RefSeq reference genomes to galaxy data libraries.')

parser.add_argument("genus", type=str, help="the genus to create a library for")
parser.add_argument('-d', '--dir', type=str, help='the RefSeq directory containing all species (overrides default)')
parser.add_argument('-k', '--key', type=str, help='the Galaxy API key to use (overrides default)')
parser.add_argument('-v', '--verbose', action="store_true", help='Print out debugging information')

# Parse args, store genus in lowercase
args = parser.parse_args()
genus = args.genus.lower()

# Override defaults for API key and RefSeq dir if we need to
if args.dir:
    REFSEQ_DIR = args.dir

# Ensure the RefSeq directory ends in a / to avoid errors later
if REFSEQ_DIR[-1] != "/":
    REFSEQ_DIR += "/"

if args.key:
    GALAXY_KEY = args.key

# Print out debugging info
if args.verbose:
    print("Galaxy URL: " + GALAXY_URL)
    print("Galaxy Key: " + GALAXY_KEY)
    print("RefSeq Directory: " + REFSEQ_DIR)
    print("Genus: " + genus)

# Check the RefSeq directory exists, exit if we can't find it
if not os.path.isdir(REFSEQ_DIR):
    printerr("ERROR: The RefSeq directory could not be found")
    sys.exit(1)

# Initiating Galaxy connection
gi = GalaxyInstance(url=GALAXY_URL, key=GALAXY_KEY)


# Make a dict of all RefSeq directories, map genus to relevant dirs
dirs = defaultdict(list)

for folder in os.listdir(REFSEQ_DIR):
    if args.verbose: print("Processing folder - " + folder)

    # Ignore hidden folders/files
    if folder[0] != ".":
        # Temp copy folder in case it starts with a _
        folder_tmp = folder

        # If folder starts with a _ then trim string
        if folder_tmp.find("_") == 0:
            folder_tmp = folder_tmp[1:]

        # Grab genus from folder name, add genus:folder pair to dict
        split_point = folder_tmp.find("_")
        dirs[folder_tmp[:split_point].lower()].append(folder)


# If we don't have the genus, error and exit
if genus not in dirs:
    printerr("ERROR: There are no genomes for your specified genus " + genus)
    sys.exit(1)


# Check for existing libraries
libraries = gi.libraries.get_libraries(deleted=False)

# Create library if it doesn't exist
if genus in [lib['name'] for lib in libraries if not lib['deleted']]:
    if args.verbose: print("Library already exists - checking it is up to date")

    # Get library - assumes theres only one library of that name
    lib = gi.libraries.get_libraries(name=genus, deleted=False)[0]
else:
    if args.verbose: print("Library doesn't exist - adding new library")
    lib = gi.libraries.create_library(genus, "Reference genomes for " + genus)


# Get all the directory names for checking later on
lib_dirs = [d['name'][1:] for d in gi.libraries.get_folders(lib['id'])]

for folder in dirs[genus]:

    # Check if folder exists, get required info if it does else create it
    if folder in lib_dirs:
        if args.verbose: print("Directory exists: " + folder)

        # Get directory information
        fldr = gi.libraries.get_folders(lib['id'], name="/" + folder)[0]

    else:
        if args.verbose: print("Adding directory to library - " + folder)
        fldr = gi.libraries.create_folder(lib['id'], folder)[0]

    for fna in os.listdir(REFSEQ_DIR + folder):

        # If file doesn't exist, add it
        if fna not in getFilesInFolder(gi.libraries.show_library(lib['id'], contents=True), folder):
            if args.verbose: print("Adding file - " + fna)

            # This makes a symbolic link instead of a copy
            gi.libraries.upload_from_galaxy_filesystem(
                library_id=lib['id'],
                filesystem_paths=REFSEQ_DIR + folder + "/" + fna,
                folder_id=fldr['id'],
                link_data_only="link_to_files")

        else:
            if args.verbose: print("File exists - " + fna)
