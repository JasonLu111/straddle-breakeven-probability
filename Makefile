.PHONY: install data phase1 options-data phase2 phase3 test

install:
	pip install -r requirements.txt

data:
	python scripts/download_data.py

phase1:
	python scripts/build_dataset.py --phase 1
	python scripts/run_statistical_tests.py

options-data:
	python scripts/download_options_data.py

phase2: options-data
	python scripts/build_dataset.py --phase 2
	python scripts/run_h2_tests.py

phase3:
	python -c "from src.models.build_model_dataset import run; [run(t) for t in ['SPY','QQQ']]"
	python scripts/train_models.py

test:
	pytest -q
