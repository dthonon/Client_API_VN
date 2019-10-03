FROM python:3.7-buster

VOLUME ["/root"]

RUN pip install Client-API-VN --no-cache-dir

CMD ["transfer_vn","--status","evn.yaml"]
