#FROM returntocorp/semgrep:0.35.0@sha256:203eefa7fef3d85e9313fd322642a78ee030188876122a0e7521fdc5c4d199c3 AS semgrep
FROM python:3.7-alpine

WORKDIR /app
COPY poetry.lock ./
COPY pyproject.toml ./

ENV INSTALLED_SEMGREP_VERSION=0.35.0

#COPY --from=semgrep /usr/local/bin/semgrep-core /tmp/semgrep-core


RUN apk add --no-cache --virtual=.build-deps build-base libffi-dev openssl-dev &&\
    apk add --no-cache --virtual=.run-deps bash git less libffi openssl &&\
    # Need to pin cryptography version to avoid Rust compiler dependency
    pip install --no-cache-dir cryptography==3.3.2 poetry==1.0.10 &&\
    pip install --no-cache-dir pipx &&\
    #PRECOMPILED_LOCATION=/tmp/semgrep-core pipx install semgrep==${INSTALLED_SEMGREP_VERSION} &&\
    poetry config virtualenvs.create false &&\
    # Don't install dev dependencies or semgrep-agent
    poetry install --no-dev --no-root &&\
    pip uninstall -y poetry &&\
    apk del .build-deps &&\
    rm -rf /root/.cache/* /tmp/*

COPY ./src/semgrep_agent /app/semgrep_agent
ENV PATH=/root/.local/bin:${PATH} \
    PYTHONPATH=/app:${PYTHONPATH}

CMD ["python", "-m", "semgrep_agent"]

ENV SEMGREP_ACTION=true\
    SEMGREP_ACTION_VERSION=v1\
    R2C_USE_REMOTE_DOCKER=1
