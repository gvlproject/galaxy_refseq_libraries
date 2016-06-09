"""
This example retrieves details of all the Data Libraries available to us and lists information on them.
Usage: python list_data_libraries.py <galaxy-url> <galaxy-API-key>
"""
from __future__ import print_function
import sys

from bioblend.galaxy import GalaxyInstance

galaxy_url = 'http://115.146.94.125/galaxy/'
galaxy_key = '76822b3132377362e5607732b2574766'

def getLibs(gi):
    libraries = gi.libraries.get_libraries()

    if len(libraries) == 0:
        print("There are no Data Libraries available.")
    else:
        print("\nData Libraries:")
        for lib_dict in libraries:
            print("{0} : {1}".format(lib_dict['name'], lib_dict['id']))





print("Initiating Galaxy connection")

gi = GalaxyInstance(url=galaxy_url, key=galaxy_key)

print("Retrieving Data Library list")

getLibs(gi)

lib = gi.libraries.create_library("test-lib")

getLibs(gi)