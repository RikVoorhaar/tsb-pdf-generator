# syntax=docker/dockerfile:1
FROM pandoc/latex:2.19
RUN apk add python3 git py3-pip ttf-liberation
WORKDIR /app
COPY app .
RUN pip3 install -r requirements.txt
RUN cat tex-packages.txt | xargs tlmgr install
