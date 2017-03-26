'''
Script to edit permissions of an existing Galaxy data library.

usage: library_permissions.py [-h] [-u URL] [-k KEY]
                              [-e [EMAILS [EMAILS ...]]] [-a] [-s] [-i] [-p]
                              [-r] [-v]
                              name

Edit permissions for an existing data library. This script will append users
by default.

positional arguments:
  name                  the name of the data library

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     the Galaxy URL
  -k KEY, --key KEY     the Galaxy API key to use (overrides default)
  -e [EMAILS [EMAILS ...]], --emails [EMAILS [EMAILS ...]]
                        A space-seperated list of emails of users.
  -a, --add_files       Give the list of users permission to add/remove files
                        to library (Default: Admin only)
  -s, --see_library     Give the list of users permission to view the library
                        (Default: Public library)
  -i, --modify_info     Give the list of users permission to edit library
                        information (Default: Admin only)
  -p, --modify_permissions
                        Give the list of users permission to add/remove files
                        to library (Default: Admin only)
  -r, --reset           Overwrite existing permissions for the specified
                        categories with the specified users. If users
                        unspecified, reset specified categories to default
                        permission level.
  -v, --verbose         Print out debugging information

NOTE: You cannot restrict access to a data library for any admin users.

'''

from __future__ import print_function
from bioblend.galaxy import GalaxyInstance

import argparse
import sys


def printerr(*args):
    '''
     Function for printing to stderr.

    :param args: The contents to be printed to stderr.
    :return: None.
    '''

    print(*args, file=sys.stderr)

def getUserIDFromEmail(email, all_users):
    """
    Function to get the Galaxy user ID given a user's email.

    :param email: The email of the user to get the ID for
    :param all_users: All galaxy users, obtained from gi.roles.get_roles()
    :return: The user ID if user exists, or None
    """
    match = next((user for user in all_users if user['name'].lower() == email.strip().lower()), None)
    if match:
        return match['id']
    return None

def modifyDict(dict, key, value, overwrite):
    """
    Function to modify a dictionary, where the value will be overwritten if overwrite is true and appended otherwise.

    :param dict: The dictionary
    :param key: The key to modify value for
    :param value: The value to append/overwrite
    :param overwrite: If true, overwrite the value at key
    :return: None.
    """

    if overwrite:
        dict[key] = value
    else:
        dict[key] += value

def getLibraryPermissions(gi, lib):
    """
    Function to get the existing galaxy data library permissions, and only return user ID's (no emails).

    :param gi: The galaxy instance object
    :param lib: The galaxy library object
    :return: A dictionary containing key:val pairs of data library permission: list of user IDs
    """
    permissions = gi.libraries.get_library_permissions(lib['id'])
    for key, val in permissions.items():
        user_ids = []
        for item in val:
            # Email at index 0, ID at index 1.
            user_ids.append(item[1])
        permissions[key] = user_ids
    return permissions


def main():
    # Default values.
    galaxy_url = 'http://127.0.0.1:8080/galaxy/'
    galaxy_key = ''

    # Get things like API Key, galaxy URL, etc from command line.
    parser = argparse.ArgumentParser(description='Edit permissions for an existing data library. This script will append users by default.')

    parser.add_argument('name', type=str, help='the name of the data library')
    parser.add_argument('-u', '--url', type=str, help='the Galaxy URL', default=galaxy_url)
    parser.add_argument('-k', '--key', type=str, help='the Galaxy API key to use (overrides default)', default=galaxy_key)

    parser.add_argument('-e', '--emails', nargs='*',
                        help='A space-seperated list of emails of users.',
                        default=[])

    parser.add_argument('-a', '--add_files', action="store_true",
                        help='Give the list of users permission to add/remove files to library (Default: Admin only)')
    parser.add_argument('-s', '--see_library', action="store_true",
                        help='Give the list of users permission to view the library (Default: Public library)')
    parser.add_argument('-i', '--modify_info', action="store_true",
                        help='Give the list of users permission to edit library information (Default: Admin only)')
    parser.add_argument('-p', '--modify_permissions', action="store_true",
                        help='Give the list of users permission to add/remove files to library (Default: Admin only)')

    parser.add_argument('-r', '--reset', action="store_true",
                        help='Overwrite existing permissions for the specified categories with the specified users. If users unspecified, reset specified categories to default permission level.')

    parser.add_argument('-v', '--verbose', action="store_true", help='Print out debugging information')


    # Parse args.
    args = parser.parse_args()

    # Ensure Galaxy URL ends in a / to avoid errors later.
    if args.url[-1] != "/": args.url += "/"


    # Print out debugging info.
    if args.verbose:
        print("Library name: " + str(args.name))
        print("Galaxy URL: " + str(args.url))
        print("Galaxy key: " + str(args.key))
        print("User list: " + str(args.emails))
        print("Reset/Override permissions: " + str(args.reset))
        print("Add files to library: " + str(args.add_files))
        print("View library: " + str(args.see_library))
        print("Modify library information: " + str(args.modify_info))
        print("Modify library permissions: " + str(args.modify_permissions))


    # Initiating Galaxy connection.
    if args.verbose: print("Connecting to Galaxy")
    gi = GalaxyInstance(url=args.url, key=args.key)

    # Get list of existing libraries.
    libraries = gi.libraries.get_libraries(deleted=False)

    # Get existing library info if it does exist, if it doesn't exist create library.
    if args.name.strip() in [lib['name'] for lib in libraries if not lib['deleted']]:
        if args.verbose: print("Library found")

        # Get library - assumes there is only one library of that name.
        lib = gi.libraries.get_libraries(name=args.name, deleted=False)[0]
    else:
        printerr("ERROR: Library not found.")


    if args.verbose: print("Editing user permissions")
    permissions = getLibraryPermissions(gi, lib)

    # Get all users.
    all_users = gi.roles.get_roles()

    # Find given users in existing users.
    user_ids = []
    for user in args.emails:
        user_id = getUserIDFromEmail(user, all_users)
        if user_id:
            if args.verbose: print("User " + user + " found")
            user_ids.append(user_id)
        else:
            print("WARNING: User " + user + " not found.")

    # For each permission, modify the permissions dict to add (or overwrite) the new user ID's.
    if args.add_files:
        modifyDict(permissions, "add_library_item_role_list", user_ids, args.reset)
    if args.see_library:
        modifyDict(permissions, "access_library_role_list", user_ids, args.reset)
    if args.modify_info:
        modifyDict(permissions, "modify_library_role_list", user_ids, args.reset)
    if args.modify_permissions:
        modifyDict(permissions, "manage_library_role_list", user_ids, args.reset)

    # Remove duplicates.
    for key, val in permissions.items():
        permissions[key] = list(set(val))

    if args.verbose: print("Permissions: " + str(permissions))

    gi.libraries.set_library_permissions(lib['id'],
                                     access_in=permissions["access_library_role_list"],
                                     modify_in=permissions["modify_library_role_list"],
                                     add_in=permissions["add_library_item_role_list"],
                                     manage_in=permissions["manage_library_role_list"])

if __name__ == "__main__":
    main()