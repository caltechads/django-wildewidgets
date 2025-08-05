FROM python:3.12-slim AS stage-1

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
    /usr/local/bin/pip install --upgrade supervisor pip "setuptools<81" wheel && \
    /usr/local/bin/python -m venv /ve

COPY requirements.txt /tmp/requirements.txt
RUN /ve/bin/pip install --upgrade pip wheel && \
    /ve/bin/pip install -r /tmp/requirements.txt

FROM python:3.12-slim AS stage-2

ENV HISTCONTROL=ignorespace:ignoredups  \
    IPYTHONDIR=/etc/ipython             \
    LANG=en_US.UTF-8                    \
    LANGUAGE=en_US.UTF-8                \
    LC_ALL=en_US.UTF-8                  \
    LOGGING_MODE=print                  \
    # Disable the pip cache to reduce layer size.
    PIP_NO_CACHE_DIR=1                  \
    PYCURL_SSL_LIBRARY=nss              \
    SHELL_PLUS=ipython                  \
    # This env var overrides other system timezone settings.
    TZ=America/Los_Angeles              \
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
    /usr/local/bin/pip install --upgrade supervisor pip "setuptools<81" wheel && \
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
ENV PATH=/ve/bin:/app:/usr/local/bin:$PATH

COPY . /app
WORKDIR /app

RUN pip install -e . && \
    pip install django-compressor && \
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
