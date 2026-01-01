import pytest
from src.data.loader import load_raw_data

def test_load_raw_data_valid():
    df = load_raw_data('hepg2')
    assert not df.empty
    from config import Config
    expected = Config.FEATURES + [Config.TARGET]
    assert all(col in df.columns for col in expected)

def test_load_raw_data_missing_file():
    with pytest.raises(FileNotFoundError):
        load_raw_data('notacell')

def test_load_raw_data_missing_column(tmp_path):
    import pandas as pd
    from config import Config
    # Cria arquivo CSV sem coluna obrigatória
    file_path = tmp_path / 'foo.csv'
    pd.DataFrame({'A': [1], 'B': [2]}).to_csv(file_path)
    Config.RAW_DATA_DIR = tmp_path
    with pytest.raises(ValueError):
        load_raw_data('foo')
