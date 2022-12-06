VERSION = 0.13.56

PACKAGE = wildewidgets_demo

#======================================================================


build:
	docker build -t ${PACKAGE}:${VERSION} .
	docker tag ${PACKAGE}:${VERSION} ${PACKAGE}:latest
	docker image prune -f

force-build:
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

.PHONY: list
list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | xargs
