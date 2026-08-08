.PHONY: install data phase1 test

install:
	pip install -r requirements.txt

data:
	python scripts/download_data.py

phase1:
	python scripts/build_dataset.py --phase 1
	python scripts/run_statistical_tests.py

test:
	pytest -q
