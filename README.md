# galaxy_refseq_libraries
Script to make data library of RefSeq reference genomes for specified genus

```usage: list_data_libraries.py [-h] [-d DIR] [-k KEY] [-v] genus```

Add RefSeq reference genomes to galaxy data libraries.

positional arguments:
```
genus   the genus to create a library for
```
optional arguments:
```
-h, --help         show this help message and exit
-d DIR, --dir DIR  the RefSeq directory containing all species
-k KEY, --key KEY  the Galaxy API key to use
-v, --verbose      Print out debugging information
```
Needs an API key in GALAXY_KEY unless specified via command line

Assumes Galaxy instance exists at localhost and refseq folder has the following structure:
```
refseq_folder/
    species/
        fna files
```
