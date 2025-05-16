VERSION = 1.1.3

PACKAGE = wildewidgets_demo

.PHONY: clean dist build force-build tag dev dev-detached devup devdown logall log exec restart docker-clean docker-destroy-db docker-destroy list  package
#======================================================================

clean:
	rm -rf *.tar.gz dist *.egg-info *.rpm
	find . -name "*.pyc" -exec rm '{}' ';'

dist: clean
	@python setup.py sdist

package:
	(cd ..; python setup.py sdist)
	cp ../dist/django-wildewidgets-${VERSION}.tar.gz django-wildewidgets.tar.gz

build:
	docker build -t ${PACKAGE}:${VERSION} .
	docker tag ${PACKAGE}:${VERSION} ${PACKAGE}:latest
	docker image prune -f

force-build: package
	docker build --no-cache -t ${PACKAGE}:${VERSION} .
	docker tag ${PACKAGE}:${VERSION} ${PACKAGE}:latest
	docker image prune -f

dev:
	docker-compose -f docker-compose.yml up

dev-detached:
	docker-compose -f docker-compose.yml up -d

down: devdown

devup:
	docker-compose -f docker-compose.yml up -d

devdown:
	docker-compose down

logall:
	docker-compose logs -f

log:
	docker logs -f wildewidgets_demo

exec:
	docker exec -it wildewidgets_demo /bin/bash

docker-clean:
	docker stop $(shell docker ps -a -q)
	docker rm $(shell docker ps -a -q)

docker-destroy-db: docker-clean
	docker volume rm wildewidgets_demo_data


.PHONY: list
list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | xargs
