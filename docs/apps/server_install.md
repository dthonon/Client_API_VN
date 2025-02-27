# Guide d'installation d'un serveur debian

Procédure d'installation sur Linux Debian 11 ou Ubuntu 21.10.

Notes :

- les lignes encadrées sont des commandes bash à exécuter
- les lignes précédées de => sont des éditions à faire manuellement
- selon l'hébergeur, certaines étapes de préparation ne sont pas nécessaires
- le texte entre \* est à remplacer par le votre
- non testé avec d'autres distributions

## 1. Préparer l'installation

Les commandes suivantes permettent de configurer la machine virtuelle
selon la localisation, ici en France, et de nommer la machine.

```bash
sudo dpkg-reconfigure tzdata
```

=> Sélectionner `Europe / Paris`

```bash
sudo dpkg-reconfigure locales
```

=> Sélectionner `fr_FR.UTF-8` et `fr_FR.UTF-8` par défaut

```bash
sudo hostnamectl set-hostname *votre_nom_de_serveur* --static
```

Les commandes suivantes mettent à jour les paquets et ajoutent
les paquets utiles.

```bash
sudo apt -y update
sudo apt -y dist-upgrade
```

## 2. Installer postgresql

L'installation depuis le dépôt debian standard est réalisée
de la manière suivante.

```bash
sudo apt -y install postgresql postgresql-contrib
sudo apt -y install postgis postgresql-postgis
```
Puis éditez le fichier de configuration :
```bash
sudo nano /etc/postgresql/16/main/postgresql.conf
```
=> changer :

```cfg
listen_addresses='*'
```

Puis éditez le fichier d'autorisation :
```bash
sudo nano /etc/postgresql/16/main/pg_hba.conf
```
=> ajouter la ligne suivante pour autoriser l'accès exterieur à postgresql.
`host all all 0.0.0.0/0 md5`

```bash
sudo systemctl reload postgresql
sudo -iu postgres
```
```plpgsql
psql
CREATE EXTENSION adminpack;
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
ALTER ROLE postgres PASSWORD '*whateveryouwant*';
CREATE ROLE xfer38 LOGIN PASSWORD '*whateveryouwant*' SUPERUSER CREATEDB CREATEROLE;
```

## 3. Sécurisation du système

L'accès au serveur est sécurisé en retirant les accès aux comptes
par défaut et installant un firewall:

```bash
sudo adduser adm_xfer
sudo usermod -a -G sudo adm_xfer
sudo nano /etc/sudoers
```
=> Modifier la ligne `%sudo   ALL=(ALL:ALL) NOPASSWD:ALL`
```bash
sudo -iu adm_xfer
nano .profile
```
=> ajouter la ligne `PATH="$PATH:/usr/local/sbin:/usr/sbin:/sbin:/bin"` en fin de fichier
```bash
mkdir .ssh
chmod 700 .ssh
nano .ssh/authorized_keys
```
=> copier la clé publique et sauvegarder
```bash
chmod 600 .ssh/authorized_keys
sudo nano /etc/ssh/sshd_config
```
=> Modifier `PermitRootLogin no`
```bash
sudo nano /etc/passwd
```
=> remplacer `/bin/bash` par `/usr/sbin/nologin` pour les comptes debian ou ubuntu et postgres
```bash
sudo apt -y install ufw
sudo ufw allow ssh
sudo ufw allow postgresql
# For development servers with additional services (developpement...), to be customized
sudo ufw allow smtp
sudo ufw allow ftp
sudo ufw allow http
sudo ufw allow https
# After adding all ports
sudo ufw enable
sudo reboot
```

## 4. Créer le compte

La création du compte de téléchargement est assurée par:

```bash
sudo adduser xfer38
```

## 5. Installer l'application

Voir README.

## 10. Optionnel

Installation serveur FTP.

```bash
sudo apt -y install proftpd
sudo nano /etc/proftpd/proftpd.conf
```
=> Mettre `UseIPv6 off`
=> Modifier `ServerName`
=> Decommenter `DefaultRoot ~` et ajouter `RootLogin off`
=> Modifier `PassivePorts 50000 50100` et `MasqueradeAddress 1.2.3.4` avec votre adresse IP
```bash
sudo ufw allow 50000:50100/tcp
```

## 11. Optionnel

Ajouter un disque supplémentaire.

```bash
sudo apt -y install lvm2
sudo cfdisk /dev/sdb
sudo pvcreate /dev/sdb1
sudo vgcreate storage /dev/sdb1
sudo lvcreate -l 100%FREE -n sharing storage
sudo mkfs.ext4 /dev/storage/sharing
sudo nano /etc/fstab
```
    => Ajouter la ligne `/dev/storage/sharing  /home/sharing  ext4  defaults  0 2`
```bash
sudo mkdir /home/sharing/
sudo chown xfer38 /home/sharing/
sudo chgrp xfer38 /home/sharing/
sudo mount /home/sharing/
```

## 12. Optionnel

Mise en place des outils de mail, surveillance...

```bash
sudo apt -y install mailutils postfix
```
=> Sélectionner `Distribution directe par SMTP (site Internet)`
=> Valeurs par défaut par la suite
```bash
sudo apt -y install opendkim opendkim-tools
sudo nano /etc/opendkim.conf
```
=> voir https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-dkim-with-postfix-on-debian-wheezy
```bash
sudo apt -y install logwatch
sudo mkdir /var/cache/logwatch
sudo cp /usr/share/logwatch/default.conf/logwatch.conf /etc/logwatch/conf/
sudo nano /etc/logwatch/conf/logwatch.conf
```
=> `MailTo = adresse@domaine.tld`
```bash
sudo apt install fail2ban
```
=> Voir https://www.digitalocean.com/community/tutorials/how-to-protect-ssh-with-fail2ban-on-debian-7
