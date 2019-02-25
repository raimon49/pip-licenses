FROM python:3.7.2-alpine
LABEL maintainer="raimon <raimon49@hotmail.com>"

WORKDIR /opt/piplicenses

COPY ./docker/requirements.txt /opt/piplicenses

RUN python3 -m venv /opt/piplicenses/myapp \
        && source /opt/piplicenses/myapp/bin/activate
RUN pip3 install -U pip \
        && pip3 install -r /opt/piplicenses/requirements.txt \
        && pip3 install -U pip-licenses

ENTRYPOINT ["pip-licenses"]
CMD ["--from-classifier"]
