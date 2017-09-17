FROM alpine:latest
MAINTAINER Matthew Gall <docker@matthewgall.com>

RUN apk add --update \
	build-base \
	python3 \
	python3-dev \
	py-pip \
	py-virtualenv \
	openssl-dev \
	libffi-dev \
	&& rm -rf /var/cache/apk/*

WORKDIR /app
COPY . /app

RUN virtualenv -p python3 /env && /env/bin/pip install -r /app/requirements.txt

EXPOSE 5000
CMD ["/env/bin/python3", "/app/app.py"]