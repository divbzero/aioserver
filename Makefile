.PHONY: install
install: venv
	. .venv/bin/activate; pip install -e .

.PHONY: test
test: install
	. .venv/bin/activate; sed -n '/^```python/,/^```/ p' < README.md | sed '/^```/d' | python

.PHONY: venv
venv:
	python3 -m venv .venv
