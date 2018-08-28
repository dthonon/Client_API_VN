#!/usr/bin/env python3
import sys
import logging
from optparse import OptionParser
import configparser
from pathlib import Path

# version of the program:
__version__= "0.1.1" #VERSION#

def script_shortname():
    """return the name of this script without a path component."""
    return os.path.basename(sys.argv[0])

def print_usage():
    """print a short summary of the scripts function."""
    print(('%-20s: Chargement dans BD Postgresql des données Biolovision '+\
           'Ecrit en python ...\n') % script_shortname())

def main(argv):
    """
    Main.
    """

    # Get options
    # command-line options and command-line help:
    usage = 'usage: %prog [options] {files}'

    parser = OptionParser(usage=usage,
                          version='%%prog %s' % __version__,
                          description='Téléchargement des données Biolovision.')

    parser.add_option('-v', '--verbose',
                      action='store_true',
                      dest='verbose',
                      help='Traces de mise au point.')

    (options, args) = parser.parse_args()
    print(options)
    # print(args)
    # sys.exit()

    if (options.verbose) :
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level = logging.DEBUG)
    else :
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level = logging.INFO)




    logging.debug('Test debug')
    logging.info('Test info')
    logging.warning('Test warning')

# Main wrapper
if __name__ == "__main__":
    main(sys.argv[1:])
