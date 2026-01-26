FROM python:3.14-slim AS stage-1

# Configure uv to run in a way that's best suited for Docker.
ENV UV_PROJECT_ENVIRONMENT=/ve \
    UV_COMPILE_BYTECODE=1      \
    UV_LINK_MODE=copy          \
    UV_PYTHON_DOWNLOADS=never

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install --yes --no-install-recommends \
        gcc g++ rustc cargo \
        # Some of our python dependencies come from github or gitlab
        git \
        # Mysql dependencies for mysqlclient
        mariadb-client libmariadb-dev pkg-config \
        # LDAP libraries for python-ldap
        libldap-dev libsasl2-dev libldap-common \
        # Various dependencies for common requirements.
        libcurl4-openssl-dev libreadline-dev libssl-dev locales-all libffi-dev libxslt1-dev \
    && \
    apt-get clean && \
    ln -sf /bin/bash /bin/sh && \
    /usr/local/bin/python -m venv /ve

RUN --mount=type=cache,target=/uv-cache \
    --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv --cache-dir=/uv-cache sync --frozen --no-install-project


FROM python:3.14-slim AS stage-2

ENV HISTCONTROL=ignorespace:ignoredups  \
    IPYTHONDIR=/etc/ipython             \
    # Add the venv's binaries, and the /app folder, to the PATH.
    PATH=/ve/bin:/app:/usr/local/bin:$PATH \
    PYCURL_SSL_LIBRARY=nss              \
    SHELL_PLUS=ipython                  \
    # This env var overrides other system timezone settings.
    TZ=America/Los_Angeles              \
    # Tell uv where the venv is, and to always copy instead of hardlink, which is needed for a mounted uv cache.
    UV_PROJECT_ENVIRONMENT=/ve          \
    UV_LINK_MODE=copy                   \
    # Tell python which venv to use.
    VIRTUAL_ENV=/ve

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install --yes --no-install-recommends \
        nginx \
        mariadb-client libmariadb-dev pkg-config \
        locales-all \
        hostname less make procps psmisc tar telnet vim wget which \
    && \
    apt-get clean && \
    ln -sf /bin/bash /bin/sh && \
    /usr/local/bin/pip install supervisor uv && \
    # Uninstall pip.
    /usr/local/bin/pip uninstall -y pip && \
    adduser --disabled-password app && \
    mkdir -p /var/tmp/nginx/client_body \
        /var/tmp/nginx/proxy \
        /var/tmp/nginx/fastcgi \
        /var/tmp/nginx/uwsgi \
        /var/tmp/nginx/scgi \
    && \
    chown -R app:app /var/tmp/nginx && \
    mkdir -p /certs && \
    openssl req -x509 -nodes \
      -subj "/C=US/ST=CA/O=Caltech/CN=localhost.localdomain" \
      -days 3650 \
      -newkey rsa:2048 \
      -keyout /certs/localhost.key \
      -out /certs/localhost.crt && \
    chown app:app /certs/*

COPY --from=stage-1 --chown=app:app /ve /ve

COPY . /app
WORKDIR /app

RUN --mount=type=cache,target=/uv-cache \
    set -x && \
    # We use --cache-dir instead of defining UV_CACHE_DIR in the env because we don't want uv to use that cache folder
    # when running while exec'd into the container, as it won't exist then.
    uv --cache-dir=/uv-cache sync --frozen && \
    python manage.py compilescss  --settings=demo.settings_docker -v0 --skip-checks  && \
    python manage.py collectstatic --settings=demo.settings_docker --noinput -v0 --link && \
    chown -R app:app /static && \
    cp etc/supervisord.conf /etc/supervisord.conf && \
    cp etc/nginx.conf /etc/nginx/nginx.conf && \
    cp etc/gunicorn_logging.conf /etc/gunicorn_logging.conf && \
    mkdir -p /etc/ipython && \
    touch /etc/ipython/__init__.py && \
    cp etc/ipython_config.py /etc/ipython/ipython_config.py && \
    chown -R app:app /etc/ipython

# Expose the app's communication port.
EXPOSE 8443

# Switch execution to the app user, so that supervisor runs as app, rather than root.
USER app

CMD ["/usr/local/bin/supervisord", "-c", "/etc/supervisord.conf"]
