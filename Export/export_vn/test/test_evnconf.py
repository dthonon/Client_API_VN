import sys
import shutil
from export_vn.evnconf import EvnConf
from pathlib import Path

# Create test site configuration file
SITE = 'tst'
shutil.copyfile(str(Path.home()) + '/Client_API_VN/Export/evn_template.ini', str(Path.home()) + '/.evn_' + SITE + '.ini')

cfg = EvnConf(SITE)

def test_site():
    assert cfg.site == SITE

def test_base_url():
    assert cfg.base_url == 'https://www.faune-xxx.org/'

def test_user_email():
    assert cfg.user_email == 'nom.prenom@example.net'

def test_user_pw():
    assert cfg.user_pw == '*evn_user_pw*'

def test_client_key():
    assert cfg.client_key == '*evn_client_key*'

def test_client_secret():
    assert cfg.client_secret == '*evn_client_secret*'

def test_file_store():
    assert cfg.file_store == 'VN_files' + '/' + SITE + '/'

def test_db_host():
    assert cfg.db_host == 'localhost'

def test_db_port():
    assert cfg.db_port == '5432'

def test_db_name():
    assert cfg.db_name == '*faune_xxx*'

def test_db_schema():
    assert cfg.db_schema == 'import'

def test_db_group():
    assert cfg.db_group == '*lpo_xxx*'

def test_db_user():
    assert cfg.db_user == '*xferxx*'

def test_db_pw():
    assert cfg.db_pw == '*evn_db_pw*'

def test_sql_scripts():
    assert cfg.sql_scripts == 'Client_API_VN/Examples/VN_sql'

def test_external1_name():
    assert cfg.external1_name == '*evn_external1_name*'

def test_external1_pw():
    assert cfg.external1_pw == '*evn_external1_pw*'
