#!/usr/bin/env python3
"""
Program managing VisioNature export to Postgresql database


"""
import sys
import logging
import argparse
import yaml
from pathlib import Path

# version of the program:
from setuptools_scm import get_version
version = get_version(root='../..', relative_to=__file__)

def main():
    """
    Main.
    """

    # Get options
    parser = argparse.ArgumentParser()
    parser.add_argument('--version',
                        help='print version number',
                        action='store_true')
    parser.add_argument('-v', '--verbose',
                        help='increase output verbosity',
                        action='store_true')
    parser.add_argument('-q', '--quiet',
                        help='reduce output verbosity',
                        action='store_true')
    parser.add_argument('-t', '--test',
                        help='test mode, with limited download volume',
                        action='store_true')
    parser.add_argument('site',
                        help='site name, used to select config file')

    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)

    logging.info('Getting data from %s', args.site)

    with open(str(Path.home()) + '/.evn_' + args.site + '.yaml', 'r') as stream:
        try:
            conf =yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    logging.info('Getting data from %s', conf['site']['evn_site'])

# Main wrapper
if __name__ == "__main__":
    main()
