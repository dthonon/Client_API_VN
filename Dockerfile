FROM python:3.7-buster

VOLUME ["/xfer"]

RUN apt update
RUN apt -y install apt-utils
RUN apt -y upgrade
RUN apt -y install nano postgresql-client
RUN pip install Client-API-VN --no-cache-dir

