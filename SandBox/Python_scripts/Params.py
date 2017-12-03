# -*- coding: utf-8 -*-
"""
Paramètres pour tous les scripts
"""
import configparser
# Using OAuth1 auth helper
from requests_oauthlib import OAuth1

# Read configuration parameters
config = configparser.ConfigParser()
config.read('~/.evn.ini')

evn_client_key = config['faune-isere.org']['evn_client_key']
evn_client_secret = config['faune-isere.org']['evn_client_secret']
evn_user_email = config['faune-isere.org']['evn_user_email']
evn_user_pw = config['faune-isere.org']['evn_user_pw']

# URL to request oauth token, not used for single query
#request_token_url = 'http://www.faune-isere.org/index.php?m_id=1200&cmd=request_token'

# URL to GET observation
protected_url = 'http://www.faune-isere.org/api/observations/'

# Using OAuth1 auth helper
oauth = OAuth1(evn_client_key,
               client_secret=evn_client_secret)

# Mandatory parameters
params = {'user_email': evn_user_email, 'user_pw': evn_user_pw}
