FROM python:3.11-slim-bookworm@sha256:94a8fee35252d06ab75856f15f12c7bae67b10e8a6da93c7fded82b2610926cd
LABEL maintainer="raimon <raimon49@hotmail.com>"

ARG APPDIR=/opt/piplicenses

WORKDIR ${APPDIR}

COPY ./docker/requirements.txt ${APPDIR}
COPY pyproject.toml piplicenses.py README.md CHANGELOG.md LICENSE MANIFEST.in py.typed /tmp/pip-licenses/

ENV VIRTUAL_ENV=${APPDIR}/myapp
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN python3 -m venv "${VIRTUAL_ENV}"

# Resolve dependencies, then replace any installed copy with the checkout's wheel.
RUN python -m pip wheel --no-cache-dir --no-deps --wheel-dir /tmp/wheels /tmp/pip-licenses \
        && python -m pip install --no-cache-dir -r requirements.txt \
        && python -m pip install --no-cache-dir /tmp/wheels/pip_licenses-*.whl \
        && python -m pip install --no-cache-dir --force-reinstall --no-deps /tmp/wheels/pip_licenses-*.whl \
        && rm -rf /tmp/pip-licenses /tmp/wheels

ENTRYPOINT ["pip-licenses"]
CMD ["--from=mixed"]
