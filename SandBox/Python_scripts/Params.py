# -*- coding: utf-8 -*-
"""
Paramètres pour tous les scripts
"""
import configparser
from pathlib import Path

# Read configuration parameters
config = configparser.ConfigParser()
config.read(str(Path.home()) + '/.evn.ini')

# Import parameters in local variables
evn_client_key = config['faune-isere.org']['evn_client_key']
evn_client_secret = config['faune-isere.org']['evn_client_secret']
evn_user_email = config['faune-isere.org']['evn_user_email']
evn_user_pw = config['faune-isere.org']['evn_user_pw']
evn_base_url = config['faune-isere.org']['evn_site']
evn_file_store = config['faune-isere.org']['evn_file_store']
