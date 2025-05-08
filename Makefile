.PHONY: install
install: venv
	. .venv/bin/activate; python3 -m pip install --upgrade pip
	. .venv/bin/activate; python3 -m pip install -e .

.PHONY: demo
demo: install
	. .venv/bin/activate; sed -n '/^```python/,/^```/ p' < README.md | sed '/^```/d' | python

.PHONY: venv
venv:
	python3 -m venv .venv
