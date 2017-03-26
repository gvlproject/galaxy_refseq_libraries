'''
 Script to make data library of local file/directory structure.
usage: directory_to_library.py [-h] [-u URL] [-k KEY] [-n NAME] [-v]
                            [-t [FILETYPES [FILETYPES ...]]] [-e]
                            directory

Make a galaxy data library from a file/directory structure.

positional arguments:
  directory             the directory to make a data library from

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     the Galaxy URL
  -k KEY, --key KEY     the Galaxy API key to use (overrides default)
  -n NAME, --name NAME  the name of the data library to create (overrides
                        default). Using an existing data library name will
                        update the existing library.
  -v, --verbose         Print out debugging information
  -t [FILETYPES [FILETYPES ...]], --filetypes [FILETYPES [FILETYPES ...]]
                        A space-seperated list of filetypes to include in the
                        data library. Defaults to fna, faa, ffn, gbk, gff
  -e, --exclude         Exclude the file types specified in -t. Defaults to
                        excluding fna, faa, ffn, gbk, gff

 Needs an API key in GALAXY_KEY unless specified via command line
 Assumes Galaxy instance exists at localhost unless otherwise specified.

'''

from __future__ import print_function
from bioblend.galaxy import GalaxyInstance

import argparse
import os
import sys


def printerr(*args):
    '''
     Function for printing to stderr.

    :param args: The contents to be printed to stderr.
    :return: None.
    '''

    print(*args, file=sys.stderr)


def getFilesInLibrary(contents):
    '''
     Function for getting a list of all files in a library.

    :param contents: The contents of the library - can be obtained with show_library(lib['id'], contents=True).
    :return: A list of file names, including their directory path (strings) within library.
    '''

    return [item['name'] for item in contents if item['type'] == 'file']


def getFilesToInclude(filepath, file_types, exclude=False):
    '''
     Function for getting a list of all files of a given type (or the inverse).

    :param filepath: The path of the folder containing the files.
    :param file_types: A list of file types you wish to include/exclude.
    :param include: True if you want to get files matching those in fileTypes,
            False if you want to exclude files matching those in fileTypes.
    :return: A list of file names (strings) within folder
    '''

    # Get all files and folders in the specified directory
    dirlist = []
    for root, dirs, files in os.walk(filepath):
        for name in files:
            dirlist.append(os.path.join(root, name).replace(filepath, ""))

    # By default, we check if the filetype is in the filetypes.
    compareFunc=lambda ftype,ftypes: ftype.endswith(tuple(ftypes))
    if exclude: # Overriding default behaviour
        compareFunc=lambda ftype,ftypes: not ftype.endswith(tuple(ftypes))

    files_to_include = []
    for fileName in dirlist:
        # Compare the file extension with the fileTypes list.
        if compareFunc(fileName, file_types):
            if fileName.split("/")[-1][0] != ".":  # Don't include hidden files.
                files_to_include.append(fileName)

    return files_to_include

def makeDirectoryOrFile(gi, lib, galaxy_parent_dir, local_parent_dir, filepath, dir_index, galaxy_url, verbose):
    """
    Recursive function for traversing a filepath, and at each step, make either a directory or a file in a
    galaxy data library. Allows us to copy a whole directory structure in a galaxy data library.

    :param gi: Galaxy instance object
    :param lib: The Galaxy library object, representing the library to create the directory structure in
    :param galaxy_parent_dir: The galaxy directory object of the parent dir of our current traversal location.
    :param local_parent_dir: The local filepath that preceeds the top-level directory of the structure we're creating.
    :param filepath: The filepath to traverse, as a list (e.g. ['refseq', 'salmonella', 'ABC.gbk'])
    :param dir_index: The index of the filepath that we're currently looking at
    :param galaxy_url: The URL of the galaxy instance
    :param verbose: True if we're outputting debugging info.
    :return: None
    """

    current_filepath = filepathToString(filepath[:dir_index + 1])
    lib_dirs = [d['name'] for d in gi.libraries.get_folders(lib['id'])]
    if dir_index == len(filepath)-1:
        makeFile(gi, lib, galaxy_parent_dir, local_parent_dir, filepath, galaxy_url, verbose)
    else:
        # Check if folder exists, get required info if it does, otherwise create it
        if current_filepath in lib_dirs:
            if verbose: print("Directory exists: " + current_filepath)

            # Get directory information
            galaxy_folder = gi.libraries.get_folders(lib['id'], name=current_filepath)[0]
        else:
            if verbose: print("Adding directory to library - " + current_filepath)
            galaxy_folder = gi.libraries.create_folder(lib['id'],
                                              current_filepath.split("/")[-1],
                                              base_folder_id=galaxy_parent_dir['id'])[0]

        dir_index += 1
        makeDirectoryOrFile(gi, lib, galaxy_folder, local_parent_dir, filepath, dir_index, galaxy_url, verbose)


def makeFile(gi, lib, galaxy_parent_dir, local_parent_dir, filepath, galaxy_url, verbose):
    """
    Function to add a file to a galaxy data library.
    If the Galaxy instance is local, it will make a symlink instead of uploading.

    :param gi: Galaxy instance object
    :param lib: The Galaxy library object, representing the library to create the directory structure in
    :param galaxy_parent_dir: The galaxy directory object of the parent dir of the file.
    :param local_parent_dir: The local filepath that preceeds the filepath param below.
    :param filepath: The filepath to traverse, as a list (e.g. ['refseq', 'salmonella', 'ABC.gbk'])
    :param galaxy_url: The URL of the galaxy instance
    :param verbose: True if we're outputting debugging info.
    :return: None
    """

    filename = filepath[-1]
    # If file doesn't exist, add it
    if filepathToString(filepath) not in getFilesInLibrary(gi.libraries.show_library(lib['id'], contents=True)):
        if verbose: print("Adding file - " + filepathToString(filepath))

        if "127.0.0.1" in galaxy_url or "localhost" in galaxy_url:
            # Local Galaxy server - create a symbolic link instead of a copy
            gi.libraries.upload_from_galaxy_filesystem(
                library_id=lib['id'],
                filesystem_paths=local_parent_dir + filepathToString(filepath),
                folder_id=galaxy_parent_dir['id'],
                link_data_only="link_to_files")
        else:
            # Remote Galaxy server - copy files from local machine
            gi.libraries.upload_file_from_local_path(
                library_id=lib['id'],
                file_local_path=local_parent_dir + filepathToString(filepath),
                folder_id=galaxy_parent_dir['id'])
    else:
        if verbose: print("File exists - " + filename)

def filepathToString(filepath):
    """
    Turn a list of a filepath into a string.
    e.g. turn ['refseq', 'salmonella', 'abc.gbk'] into '/refseq/salmonella/abc.gbk'

    :param filepath: The filepath as a list
    :return: The string representing the filepath.
    """

    return "/"+"/".join(filepath)

def main():
    # Default values.
    galaxy_url = 'http://127.0.0.1:8080/galaxy/'
    galaxy_key = '41af1965d4573a6e253b3fbc692b8d90'
    file_types=['fna', 'faa', 'ffn', 'gbk', 'gff']

    # Get things like API Key, RefSeq directory and genus from command line.
    parser = argparse.ArgumentParser(description='Make a galaxy data library from a file/directory structure.')

    parser.add_argument('directory', type=str, help='the directory to make a data library from')
    parser.add_argument('-u', '--url', type=str, help='the Galaxy URL', default=galaxy_url)
    parser.add_argument('-k', '--key', type=str, help='the Galaxy API key to use (overrides default)', default=galaxy_key)
    parser.add_argument('-n', '--name', type=str, help='the name of the data library to create (overrides default). Using an existing data library name will update the existing library.')
    parser.add_argument('-v', '--verbose', action="store_true", help='Print out debugging information')
    parser.add_argument('-t', '--filetypes', nargs='*', help='A space-seperated list of filetypes to include in the data library. Defaults to fna, faa, ffn, gbk, gff', default=file_types)
    parser.add_argument('-e', '--exclude', action='store_true', help='Exclude the file types specified in -t. Defaults to excluding fna, faa, ffn, gbk, gff')

    # Parse args.
    args = parser.parse_args()

    # Renaming for readability.
    local_directory = args.directory
    galaxy_url = args.url
    galaxy_key = args.key
    file_types = args.filetypes
    possible_lib_name = args.name


    # Ensure the local directory and Galaxy URL end in a / to avoid errors later.
    if local_directory[-1] != "/": local_directory += "/"
    if galaxy_url[-1] != "/": galaxy_url += "/"


    # Print out debugging info.
    if args.verbose:
        print("Local directory: " + local_directory)
        print("Galaxy URL: " + galaxy_url)
        print("Galaxy key: " + galaxy_key)
        print("File types: " + str(file_types))
        print("Exclude: " + str(args.exclude))

    # Check the RefSeq directory exists, exit if we can't find it.
    if not os.path.isdir(local_directory):
        printerr("ERROR: The directory could not be found at " + local_directory)
        sys.exit(1)

    # Initiating Galaxy connection.
    if args.verbose: print("Connecting to Galaxy")
    gi = GalaxyInstance(url=galaxy_url, key=galaxy_key)

    # Get list of existing libraries.
    libraries = gi.libraries.get_libraries(deleted=False)

    # Set the library name if it's not set.
    if not possible_lib_name:
        possible_lib_name = [x.strip() for x in local_directory.split("/") if x][-1]

    if args.verbose: print("Library name: " + possible_lib_name)

    # Get existing library info if it does exist, if it doesn't exist create library.
    if possible_lib_name in [lib['name'] for lib in libraries if not lib['deleted']]:
        if args.verbose: print("Library already exists - checking it is up to date")

        # Get library - assumes there is only one library of that name.
        lib = gi.libraries.get_libraries(name=possible_lib_name, deleted=False)[0]
    else:
        if args.verbose: print("Library doesn't exist - adding new library")
        lib = gi.libraries.create_library(possible_lib_name,
                                          "Data library created from directory: " + possible_lib_name)

    # Get list of files and directories to include.
    filepaths_to_include = getFilesToInclude(local_directory, file_types, args.exclude)

    # For each species specified, go through each folder and add appropriate files
    galaxy_parent_dir = gi.libraries.get_folders(lib['id'], name="/")[0]

    # Add each file and directory.
    for filepath in filepaths_to_include:
        makeDirectoryOrFile(gi, lib, galaxy_parent_dir, local_directory, filepath.split("/"), 0,
                            galaxy_url, args.verbose)

if __name__ == "__main__":
    main()