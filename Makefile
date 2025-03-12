RAWVERSION = $(filter-out __version__ = , $(shell grep __version__ wildewidgets/__init__.py))
VERSION = $(strip $(shell echo $(RAWVERSION)))

PACKAGE = django-wildewidgets

clean:
	rm -rf *.tar.gz dist build *.egg-info *.rpm
	find . -name "*.pyc" | xargs rm
	find . -name "__pycache__" | xargs rm -rf

version:
	@echo $(VERSION)

dist: clean
	@python -m build

pypi: dist
	@twine upload dist/*

tox:
	# create a tox pyenv virtualenv based on 2.7.x
	# install tox and tox-pyenv in that ve
	# actiave that ve before running this
	@tox
