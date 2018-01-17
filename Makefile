.PHONY: _upgrade_setuptools uninstall install release sdist clean

RM = rm -rf
PYTHON = python3.6


_upgrade_setuptools:
	pip install --upgrade --upgrade-strategy eager setuptools


uninstall: _upgrade_setuptools
	-pip uninstall -y aiopluggy


install: uninstall
	pip install -e .[dev,docs,test]


sdist: clean
	$(PYTHON) setup.py sdist


release: clean
	$(PYTHON) setup.py sdist upload


clean:
	@$(RM) .eggs aiopluggy.egg-info dist .pytest_cache .coverage
	@find . -not -path "./.venv/*" -and \( \
		-name "*.pyc" -or \
		-name "__pycache__" -or \
		-name "*.pyo" -or \
		-name "*.so" -or \
		-name "*.o" -or \
		-name "*~" -or \
		-name "._*" -or \
		-name "*.swp" -or \
		-name "Desktop.ini" -or \
		-name "Thumbs.db" -or \
		-name "__MACOSX__" -or \
		-name ".DS_Store" \
	\) -delete
