.PHONY: install sample data train test lint serve docker

install:
	pip install -r requirements-dev.txt

sample:            ## synthetic data for local testing / CI
	python scripts/make_sample_data.py --rows 3000 --out data/sample_orders.csv

data:              ## real DataCo dataset from Kaggle
	./scripts/download_data.sh

train:
	PYTHONPATH=src python -m supply_chain.train --data data/DataCoSupplyChainDataset.csv

test:
	pytest -q

lint:
	ruff check .

serve:
	PYTHONPATH=src:. uvicorn api.main:app --reload

docker:
	docker build -t supply-chain-exception-detector .
	docker run --rm -p 8000:8000 supply-chain-exception-detector
