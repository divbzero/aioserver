.PHONY: install
install: venv
	. .venv/bin/activate; python3 -m pip install --upgrade pip
	. .venv/bin/activate; python3 -m pip install -e .

.PHONY: demo
demo: install
	. .venv/bin/activate; sed -n '/^```python/,/^```/ p' < README.md | sed '/^```/d' | python

.PHONY: test
test: install
	. .venv/bin/activate; sed -n '/^```python/,/^```/ p' < README.md | sed '/^```/d' | python & sleep 3 ; kill $$!

.PHONY: build
build: test
	. .venv/bin/activate; python3 -m pip install --upgrade build
	. .venv/bin/activate; python3 -m build

.PHONY: publish
publish: build
	. .venv/bin/activate; python3 -m pip install --upgrade twine
	. .venv/bin/activate; python3 -m twine upload dist/*

.PHONY: clean
clean:
	rm -rf aioserver/__pycache__ aioserver.egg-info dist

.PHONY: venv
venv:
	python3 -m venv .venv
