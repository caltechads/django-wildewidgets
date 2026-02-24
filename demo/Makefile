VERSION = 1.2.8

PACKAGE = wildewidgets_demo

#======================================================================

clean::
	rm -rf *.tar.gz dist *.egg-info *.rpm
	find . -name "*.pyc" -exec rm '{}' ';'

dist:: clean
	@uv build --sdist

package::
	(cd ..; uv build --sdist)
	cp ../dist/django-wildewidgets-${VERSION}.tar.gz django-wildewidgets.tar.gz

build::
	docker build -t ${PACKAGE}:${VERSION} .
	docker tag ${PACKAGE}:${VERSION} ${PACKAGE}:latest
	docker image prune -f

force-build:: package
	docker build --no-cache -t ${PACKAGE}:${VERSION} .
	docker tag ${PACKAGE}:${VERSION} ${PACKAGE}:latest
	docker image prune -f

dev::
	docker-compose -f docker-compose.yml up

dev-detached::
	docker-compose -f docker-compose.yml up -d

down:: devdown

devup::
	docker-compose -f docker-compose.yml up -d

devdown::
	docker-compose down

logall::
	docker-compose logs -f

log::
	docker logs -f wildewidgets_demo

exec::
	docker exec -it wildewidgets_demo /bin/bash

docker-clean::
	docker stop $(shell docker ps -a -q)
	docker rm $(shell docker ps -a -q)

docker-destroy-db:: docker-clean
	docker volume rm wildewidgets_demo_data


list::
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | xargs
