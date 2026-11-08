FROM --platform="linux/${TARGETARCH}" python:3.14-slim-trixie AS pip-licenses
# See:
# https://hub.docker.com/layers/library/python/3.14-slim-trixie/images/
# https://github.com/docker-library/python/blob/master/3.14/slim-trixie/Dockerfile
# https://github.com/docker-library/python/blob/master/LICENSE
# (circa: 2026.09.12 -- commit 8f2cb2e1c9cae4d8f772fe61f1427c96acea3257)
# See Also:
# https://hub.docker.com/layers/library/debian/trixie-slim/images/
# https://hub.docker.com/_/debian#license (and https://www.debian.org/social_contract#guidelines)
# (circa 2026.09.12)

# Set inherited values
LABEL org.opencontainers.image.title="pip-licenses"
LABEL org.opencontainers.image.description="Base image with pip-licenses installed."
# pip-licences under: (MIT) https://github.com/raimon49/pip-licenses/blob/master/LICENSE
# python3.14 image under: (MIT) https://github.com/docker-library/python/blob/master/LICENSE
# python under: (PSF) https://docs.python.org/3/license.html#terms-and-conditions-for-accessing-or-otherwise-using-python
# slim-trixie image under: (?) https://hub.docker.com/_/debian#license
LABEL org.opencontainers.image.licenses="MIT AND ((GPL-2.0-or-later OR GPL-3.0) OR (BSD-1-Clause OR BSD-2-Clause OR BSD-3-Clause OR BSD-4-Clause) OR Artistic-2.0)"

LABEL version="6.0"
LABEL maintainer="reactive-firewall <reactive-firewall@users.noreply.github.com>"

ARG APPDIR=/opt/piplicenses

WORKDIR ${APPDIR}

# when building downstream images include requirements
ONBUILD COPY ./docker/requirements.txt ${APPDIR}

SHELL ["/bin/bash", "-c"]

ENV PIP_ROOT_USER_ACTION=ignore

RUN python3 -m venv ${APPDIR}/myapp \
        && source ${APPDIR}/myapp/bin/activate

RUN pip3 install -U pip \
        && pip3 install -U pip-licenses

# when building downstream images update pip-licenses and install included requirements
ONBUILD RUN pip3 install -r ${APPDIR}/requirements.txt \
        && pip3 install -U pip-licenses

ENTRYPOINT ["pip-licenses"]
CMD ["--from=mixed"]
