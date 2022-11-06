FROM python:3.11-slim-bullseye
LABEL maintainer="raimon <raimon49@hotmail.com>"

ARG APPDIR=/opt/piplicenses

WORKDIR ${APPDIR}

COPY ./docker/requirements.txt ${APPDIR}

SHELL ["/bin/bash", "-c"]

ENV PIP_ROOT_USER_ACTION=ignore

RUN python3 -m venv ${APPDIR}/myapp \
        && source ${APPDIR}/myapp/bin/activate

RUN pip3 install -U pip \
        && pip3 install -r ${APPDIR}/requirements.txt \
        && pip3 install -U pip-licenses

ENTRYPOINT ["pip-licenses"]
CMD ["--from=mixed"]
