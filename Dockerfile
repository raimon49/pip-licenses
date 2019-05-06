FROM python:3.7.2-alpine
LABEL maintainer="raimon <raimon49@hotmail.com>"

ARG APPDIR=/opt/piplicenses

WORKDIR ${APPDIR}

COPY ./docker/requirements.txt ${APPDIR}

RUN python3 -m venv ${APPDIR}/myapp \
        && source ${APPDIR}/myapp/bin/activate

RUN pip3 install -U pip \
        && pip3 install -r ${APPDIR}/requirements.txt \
        && pip3 install -U pip-licenses

ENTRYPOINT ["pip-licenses"]
CMD ["--from=classifier"]
