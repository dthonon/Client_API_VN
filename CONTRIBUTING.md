# Client_API_VN

Python application that transfers data from Biolovision/VisoNature web sites to a local Postgresql database.

## Architecture
WIP

## Translating
Messages must be written in English, surrounded by _(). 
Currently, a French version is also provided and must be updated as new messages are added. To translate new messages, follow this process:
```shell
cd $HOME/Client_API_VN/export_vn
python3 setup.py extract_messages --out locale/transfer_vn.pot
python3 setup.py update_catalog -l fr -i locale/transfer_vn.pot -o locale/fr_FR/LC_MESSAGES/transfer_vn.po
```
Translate new messages by editing ```locale/fr_FR/LC_MESSAGES/transfer_vn.po``` and finalize by:
```shell
python3 setup.py compile_catalog --directory locale/ --locale fr_FR --domain transfer_vn
```