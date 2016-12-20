'''
 Script to make data library of RefSeq reference genomes for specified genus (or species)
 usage: refseq_to_library.py [-h] [-s SPECIES] [-u URL] [-d DIR] [-k KEY] [-v] genus

 Add RefSeq reference genomes to galaxy data libraries.

 positional arguments:
  genus                 the genus to create a library for

 optional arguments:
   -h, --help            show this help message and exit
   -s SPECIES, --species SPECIES     the species to create the library for
   -u URL, --url URL     the galaxy URL
   -d DIR, --dir DIR     the RefSeq directory containing all species
   -k KEY, --key KEY     the Galaxy API key to use
   -v, --verbose         Print out debugging information

 Needs an API key in GALAXY_KEY unless specified via command line
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


def printerr(*args):
    '''
     Function for printing to stderr

    :param args: The contents to be printed to stderr
    :return: None
    '''

    print(*args, file=sys.stderr)


def getFilesInLibraryFolder(contents, folder):
    '''
     Function for getting a list of all files in a library's folder.

    :param contents: The contents of the library - can be obtained with show_library(lib['id'], contents=True)
    :param folder: The name of the folder (as a string)
    :return: A list of file names (strings) within folder
    '''

    file_names = []
    for item in contents:
        # Split file path
        filepath = item['name'].split('/')

        # Check if file and inside folder, if so, add to list
        if item['type'] == 'file' and filepath[1] == folder:
            file_names.append(filepath[2])

    return file_names

def getFilesToInclude(filePath, fileTypes, exclude=False):
    '''
     Function for getting a list of all files of a given type (or the inverse).

    :param filePath: The path of the folder containing the files.
    :param fileTypes: A list of file types you wish to include/exclude.
    :param include: True if you want to get files matching those in fileTypes,
            False if you want to exclude files matching those in fileTypes.
    :return: A list of file names (strings) within folder
    '''

    # By default, we check if the filetype is in the filetypes.
    compareFunc=lambda ftype,ftypes: ftype.endswith(tuple(ftypes))
    if exclude: # Overriding default behaviour
        compareFunc=lambda ftype,ftypes: not ftype.endswith(tuple(ftypes))

    files_to_include = []
    for fileName in os.listdir(filePath):
        # Compare the file extension with the fileTypes list.
        if compareFunc(fileName, fileTypes):
            files_to_include.append(fileName)

    return files_to_include

if __name__ == "__main__":
    # Default values
    GALAXY_URL = 'http://127.0.0.1:8080/galaxy/'
    GALAXY_KEY = ''
    REFSEQ_DIR = '/mnt/galaxyIndices/Bacteria/'

    # Get things like API Key, RefSeq directory and genus from command line
    parser = argparse.ArgumentParser(description='Add RefSeq reference genomes to galaxy data libraries.')

    parser.add_argument("genus", type=str, help="the genus to create a library for")
    parser.add_argument('-s', '--species', type=str, help='the species to create the library for')
    parser.add_argument('-u', '--url', type=str, help='the galaxy URL')
    parser.add_argument('-d', '--dir', type=str, help='the RefSeq directory containing all species (overrides default)')
    parser.add_argument('-k', '--key', type=str, help='the Galaxy API key to use (overrides default)')
    parser.add_argument('-v', '--verbose', action="store_true", help='Print out debugging information')
    parser.add_argument('-t', '--filetypes', nargs='*', help='A list of filetypes to include in the data library. Defaults to fna, faa, ffn, gbk, gff')
    parser.add_argument('-e', '--exclude', action='store_true', help='Exclude the file types specified in -t. Defaults to excluding fna, faa, ffn, gbk, gff')

    # Parse args, store genus in lowercase
    args = parser.parse_args()
    genus = args.genus.lower()
    species = ''
    fileTypes=['fna', 'faa', 'ffn', 'gbk', 'gff']

    # Override defaults for Species, URL, API key and RefSeq dir if we need to
    if args.species:
        species = args.species.lower()

    if args.url:
        GALAXY_URL = args.url

    if args.dir:
        REFSEQ_DIR = args.dir

    if args.filetypes:
        fileTypes = args.filetypes        

    # Ensure the RefSeq directory and Galaxy URL end in a / to avoid errors later
    if REFSEQ_DIR[-1] != "/": REFSEQ_DIR += "/"
    if GALAXY_URL[-1] != "/": GALAXY_URL += "/"

    if args.key:
        GALAXY_KEY = args.key

    # Print out debugging info
    if args.verbose:
        print("Galaxy URL: " + GALAXY_URL)
        print("Galaxy Key: " + GALAXY_KEY)
        print("RefSeq Directory: " + REFSEQ_DIR)
        print("Genus: " + genus)
        print("Species: " + species)

    # Check the RefSeq directory exists, exit if we can't find it
    if not os.path.isdir(REFSEQ_DIR):
        printerr("ERROR: The RefSeq directory could not be found at " + REFSEQ_DIR)
        sys.exit(1)

    # Initiating Galaxy connection
    gi = GalaxyInstance(url=GALAXY_URL, key=GALAXY_KEY)


    # Make a dict of all genus/species/RefSeq directories, map genus to a dict of species:folder pairs
    dirs = defaultdict(lambda : defaultdict(list))

    for folder in os.listdir(REFSEQ_DIR):
        if args.verbose: print("Processing folder - " + folder)

        # Ignore hidden folders/files
        if folder[0] != ".":
            # Temp copy folder in case it starts with a _
            folder_tmp = folder

            # If folder starts with a _ then trim string
            if folder_tmp.find("_") == 0:
                folder_tmp = folder_tmp[1:]

            # Grab genus from folder name, add species:folder pair to genus dict
            split_point = folder_tmp.split("_")
            if len(split_point) > 2:
                dirs[split_point[0].lower()][split_point[1].lower()].append(folder)


    # If we don't have the genus, error and exit
    if genus not in dirs:
        printerr("ERROR: There are no genomes for your specified genus " + genus)
        sys.exit(1)

    # If we don't have the species, error and exit
    if species and species not in dirs[genus].keys():
        printerr("ERROR: There are no genomes for your specified species " + species)
        sys.exit(1)

    # Check for existing libraries
    libraries = gi.libraries.get_libraries(deleted=False)

    # Determine the library name - if species is not specified, nothing is added and trailing whitespace trimmed
    possible_lib_name = genus + " " + species
    possible_lib_name = possible_lib_name.strip()

    # Get existing library info if it does exist, if it doesn't exist create library
    if possible_lib_name in [lib['name'] for lib in libraries if not lib['deleted']]:
        if args.verbose: print("Library already exists - checking it is up to date")

        # Get library - assumes there is only one library of that name
        lib = gi.libraries.get_libraries(name=possible_lib_name, deleted=False)[0]
    else:
        if args.verbose: print("Library doesn't exist - adding new library")
        lib = gi.libraries.create_library(possible_lib_name, "Reference genomes for " + possible_lib_name)

    # Species needs to be an iterable - ensure it is
    if species:
        # If species exists, put it in a list
        species = [species]
    else:
        # If it was unspecified, make it a list of all the possible species
        species = list(dirs[genus].keys())

    # Get all the directory names for checking later on
    lib_dirs = [d['name'][1:] for d in gi.libraries.get_folders(lib['id'])]

    # For each species specified, go through each folder and add appropriate files
    for spc in species:
        for folder in dirs[genus][spc]:

            # Check if folder exists, get required info if it does, otherwise create it
            if folder in lib_dirs:
                if args.verbose: print("Directory exists: " + folder)

                # Get directory information
                fldr = gi.libraries.get_folders(lib['id'], name="/" + folder)[0]

            else:
                if args.verbose: print("Adding directory to library - " + folder)
                fldr = gi.libraries.create_folder(lib['id'], folder)[0]

            for fna in getFilesToInclude(REFSEQ_DIR + folder, fileTypes, args.exclude):

                # If file doesn't exist, add it
                if fna not in getFilesInLibraryFolder(gi.libraries.show_library(lib['id'], contents=True), folder):
                    if args.verbose: print("Adding file - " + fna)

                    if "127.0.0.1" in GALAXY_URL or "localhost" in GALAXY_URL:
                        # Local Galaxy server - create a symbolic link instead of a copy
                        gi.libraries.upload_from_galaxy_filesystem(
                            library_id=lib['id'],
                            filesystem_paths=REFSEQ_DIR + folder + "/" + fna,
                            folder_id=fldr['id'],
                            link_data_only="link_to_files")
                    else:
                        # Remote Galaxy server - copy files from local machine
                        gi.libraries.upload_file_from_local_path(
                            library_id=lib['id'],
                            file_local_path=REFSEQ_DIR + folder + "/" + fna,
                            folder_id=fldr['id'])
                else:
                    if args.verbose: print("File exists - " + fna)
