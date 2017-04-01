FROM gliderlabs/alpine:latest
MAINTAINER Matthew Gall <docker@matthewgall.com>

WORKDIR /app
COPY . /app

RUN apk add --update \
	build-base \
	git \
	python \
	python-dev \
	py-pip \
	py-virtualenv \
	&& rm -rf /var/cache/apk/* \
	&& virtualenv /env \
	&& /env/bin/pip install -r /app/requirements.txt

EXPOSE 5000
CMD ["/env/bin/python", "application.py"]