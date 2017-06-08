FROM python:2.7-alpine
MAINTAINER Breyten Ernsting <breyten@openstate.eu>

# Install system requirements
RUN apk add --update build-base git tzdata libxml2-dev libxslt-dev ffmpeg-dev \
  zlib-dev openssl-dev

WORKDIR /opt/opendataornot/
ADD . /opt/opendataornot
RUN pip install --no-cache-dir -r /opt/opendataornot/requirements.txt

# Cleanup
RUN cp /usr/share/zoneinfo/Europe/Amsterdam /etc/localtime \
  && echo "Europe/Amsterdam" > /etc/timezone \
  && apk del build-base git tzdata

RUN find . -delete

CMD ./server.py
