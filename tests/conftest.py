import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from make_sample_data import make  # noqa: E402


@pytest.fixture(scope="session")
def sample_csv(tmp_path_factory) -> Path:
    path = tmp_path_factory.mktemp("data") / "sample.csv"
    make(1500, seed=1).to_csv(path, index=False, encoding="cp1252")
    return path


@pytest.fixture(scope="session")
def trained_model_dir(sample_csv, tmp_path_factory) -> Path:
    from supply_chain.train import train

    model_dir = tmp_path_factory.mktemp("models")
    train(sample_csv, model_dir)
    return model_dir
