# -*- coding: utf-8 -*-
"""
Paramètres pour tous les scripts
"""
import configparser
from pathlib import Path

# Read configuration parameters
config = configparser.ConfigParser()
config.read(str(Path.home()) + '/.evn_faune-isere.org.ini')

# Import parameters in local variables
evn_client_key = config['site']['evn_client_key']
evn_client_secret = config['site']['evn_client_secret']
evn_user_email = config['site']['evn_user_email']
evn_user_pw = config['site']['evn_user_pw']
evn_base_url = config['site']['evn_site']
evn_file_store = config['site']['evn_file_store'] 
