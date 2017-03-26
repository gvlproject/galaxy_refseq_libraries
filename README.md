# galaxy_refseq_libraries

Script to make data library of local file/directory structure.

```
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
```

- Needs an API key in galaxy_key variable, unless specified via command line.
- Assumes Galaxy instance exists at localhost unless otherwise specified (see section below).
-

### Example use

```
python directory_to_library.py test/test_directory -u http://116.156.70.12/galaxy -k 123ABC456
```
Will make a data library called 'test_directory' on the Galaxy instance at http://116.156.70.12/galaxy

```
python directory_to_library.py test/test_directory -u http://116.156.70.12/galaxy -k 123ABC456 -n MyLibrary
```
Will make a data library called 'MyLibrary' on the Galaxy instance at http://116.156.70.12/galaxy

```
python directory_to_library.py test/test_directory -u http://116.156.70.12/galaxy -k 123ABC456 -n MyLibrary -t fna faa
```
Will make a data library called 'MyLibrary' on the Galaxy instance at http://116.156.70.12/galaxy
only including files with .fna or .faa extensions.

```
python directory_to_library.py test/test_directory -u http://116.156.70.12/galaxy -k 123ABC456 -n MyLibrary -t fna faa -e
```
Will make a data library called 'MyLibrary' on the Galaxy instance at http://116.156.70.12/galaxy
including all files except those with .fna or .faa extensions.

### Adding to a remote Galaxy server
Ensure you specify the Galaxy URL using the `-u URL` or `--url URL` options.

### Updating an existing Galaxy data library
Ensure you specify the data library name you wish to update using the `-n NAME` or `--name NAME` options.
