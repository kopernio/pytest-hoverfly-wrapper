test:
	py.test -s -q ./tests/

vtest:
	py.test -s ./tests/

cov cover coverage:
	py.test -s ./tests/ --cov=pytest_hoverfly_wrapper --cov=tests --cov-report=html --cov-report=xml --cov-report=term
	@echo "open file://`pwd`/coverage/index.html"

clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -f `find . -type f -name '@*' `
	rm -f `find . -type f -name '#*#' `
	rm -f `find . -type f -name '*.orig' `
	rm -f `find . -type f -name '*.rej' `
	rm -f .coverage
	rm -rf coverage
	rm -rf build
	rm -rf cover
	make -C docs clean
	python setup.py clean

.PHONY: all build venv test vtest testloop cov clean
