'''

'''
from __future__ import print_function
from collections import defaultdict
import os
import sys

from bioblend.galaxy import GalaxyInstance

GALAXY_URL = 'http://127.0.0.1/galaxy/'
GALAXY_KEY = '76822b3132377362e5607732b2574766'
REFSEQ_DIR = '/mnt/galaxyIndices/Bacteria/'
GENUS = 'Acetobacter'.lower()

if len(sys.argv) > 1:
    #get things like URL, KEY, REFSEQ_DIR and GENUS
    pass


# Initiating Galaxy connection

gi = GalaxyInstance(url=GALAXY_URL, key=GALAXY_KEY)

# Get a dict of all RefSeq directories
dirs = defaultdict(list)

for folder in os.listdir(REFSEQ_DIR):
    if folder[0] != ".":
        folder_tmp = folder

        if folder_tmp.find("_") == 0:
            folder_tmp = folder_tmp[1:]

        split_point = folder_tmp.find("_")
        dirs[folder_tmp[:split_point].lower()].append(folder)

if GENUS not in dirs:
    print("There are no results for your specified genus " + GENUS)
    SystemExit(1)



# Check for existing libraries
libraries = gi.libraries.get_libraries()

# NOTE: THIS IS A DEBUGGING STEP
# todo: change this code 
if GENUS in [lib['name'] for lib in libraries]:
    lib_id = gi.libraries.get_libraries(name=GENUS)[0]['id']
    gi.libraries.delete_library(lib_id)

if GENUS not in libraries:
    # Create library
    new_lib = gi.libraries.create_library(GENUS, "Reference genomes for " + GENUS)

    # Create folders, upload files
    for folder in dirs[GENUS]:
        fldr = gi.libraries.create_folder(new_lib['id'], folder)[0]
        for fna in os.listdir(REFSEQ_DIR + folder):
            gi.libraries.upload_from_galaxy_filesystem(
                library_id=new_lib['id'],
                filesystem_paths=REFSEQ_DIR + folder + "/" + fna,
                folder_id=fldr['id'],
                link_data_only="link_to_files")
