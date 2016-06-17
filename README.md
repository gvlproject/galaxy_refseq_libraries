# galaxy_refseq_libraries
Script to make data library of RefSeq reference genomes for specified genus

``` usage: refseq_to_library.py [-h] [-s SPECIES] [-u URL] [-d DIR] [-k KEY] [-v] genus

 Add RefSeq reference genomes to galaxy data libraries.

 positional arguments:
  genus                 the genus to create a library for

 optional arguments:
   -h, --help            show this help message and exit
   -s SPECIES, --species SPECIES     the species to create the library for
   -u URL, --url URL     the galaxy URL
   -d DIR, --dir DIR     the RefSeq directory containing all species
   -k KEY, --key KEY     the Galaxy API key to use

```
Needs an API key in GALAXY_KEY unless specified via command line

If species is specified, a library will be made with all refseq data for that species.
If species is unspecified, a library will be made with all species in the genus.
The refseq folder hierarchy is preserved in the library regardless.

Assumes refseq folder has the following structure:
```
refseq_folder/
    species/
        fna files
```

### Adding to a remote Galaxy server
Ensure you specify the Galaxy URL using the `-u URL` or `--url URL` options.



