#!/usr/bin/env bash
# Download the DataCo Smart Supply Chain dataset from Kaggle (~95 MB).
# Requires a Kaggle API token: https://www.kaggle.com/docs/api
set -euo pipefail
mkdir -p data
pip install --quiet kaggle
kaggle datasets download -d shashwatwork/dataco-smart-supply-chain-for-big-data-analysis -p data --unzip
ls -lh data/DataCoSupplyChainDataset.csv
