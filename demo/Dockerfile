FROM public.ecr.aws/m3v9w5i2/caltech-imss-ads/amazonlinux2-python3.10

USER root

ENV LC_ALL=en_US.utf8 LANG=en_US.utf8 PYCURL_SSL_LIBRARY=nss

RUN yum -y update && \
    yum -y install \
        gcc \
        glibc-locale-source \
        glibc-langpack-en \
        git \
        libcurl-devel \
        openssl-devel \
        # Even though we don't always use Apache in these apps, mod_ssl installs certs that we need.
        mod_ssl \
        # We need these mysql packages for python to be able to connect yo mysql, and for `manage.py dbshell` to work.
        mysql-devel \
        mysql \
        # Useful unix utilities that don't come with the base CentOS 7 image.
        hostname \
        procps \
        psmisc \
        which \
    # Cleanup for yum, as suggested by yum itself.
    && yum -y clean all && \
    rm -rf /var/cache/yum && \
    # Install nginx from amazon-linux-extras -- you can't get it through straight yum
    amazon-linux-extras install nginx1 && \
    # Set up the UTF-8 locale so that shelling into the container won't spam you with locale errors.
    localedef -i en_US -f UTF-8 en_US.UTF-8 && \
    # Install supervisor globally
    /opt/python/bin/pip3.10 install supervisor && \
    # Create the virtualenv. Note that we NEED to use `python3`, here, since `python` is currently py2.7. Once we set
    # up the PATH on the next command, `python` becomes py3.6.
    /opt/python/bin/python3.10 -m venv /ve && \
    # Add the user under which gunicorn will run.
    adduser -r gunicorn

# Ensure that we run the pip and python that are in the virtualenv, rather than the system copies.
ENV PATH /ve/bin:/opt/python/3.10/bin:$PATH
# Install the latest pip and our dependencies into the virtualenv.  We do this
# before copying the codebase so that minor code changes don't force a rebuild
# of the entire virtualenv.
COPY requirements.txt /tmp/requirements.txt
COPY django-wildewidgets.tar.gz /tmp/django-wildewidgets.tar.gz
RUN pip install --upgrade pip wheel && \
    pip install -r /tmp/requirements.txt && \
    pip install /tmp/django-wildewidgets.tar.gz && \
    # Purge the pip cache, which can save us a good few megabytes in the docker image.
    rm -rf `pip cache dir`

COPY . /app
WORKDIR /app

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Install our app into the ve, symlink static resources, copy settings files and certs into place, etc.
RUN pip install -e . && \
    # precompile the sass files
    pip3 install django-compressor && \
    python manage.py compilescss  --settings=demo.settings_docker -v0 --skip-checks  && \
    # Run collectstatic to symlink all the static files into /static, which is where the webserver expects them.
    python manage.py collectstatic --settings=demo.settings_docker --noinput -v0 --link && \
    chown -R nginx:nginx /static && \
    # Uncomment this if your project requires internationalization.
    # python manage.py compilemessages --settings=demo.settings_docker && \
    # Copy/create/delete various config files and folders.
    cp etc/supervisord.conf /etc/supervisord.conf && \
    cp etc/nginx.conf /etc/nginx/nginx.conf && \
    cp etc/gunicorn_logging.conf /etc/gunicorn_logging.conf && \
    # generate the default certs
    /usr/libexec/httpd-ssl-gencerts && \
    mkdir /certs && \
    cp /etc/pki/tls/private/localhost.key /certs && \
    cp /etc/pki/tls/certs/localhost.crt /certs && \
    chmod a+r /certs/* && \
    # Create an iPython profile and then replace the default config with our own, which enables automatic code reload.
    ipython profile create && \
    cp etc/ipython_config.py /root/.ipython/profile_default/ipython_config.py

# Expose the ports we configured gunicorn to listen to.
EXPOSE 443

CMD ["/opt/python/bin/supervisord", "-c", "/etc/supervisord.conf"]
