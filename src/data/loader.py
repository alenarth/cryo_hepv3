import pandas as pd
from pathlib import Path

RAW_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
FEATURES = ['% DMSO', 'TREHALOSE']
TARGET = '% QUEDA DA VIABILIDADE'

def load_raw_data(cell_type: str) -> pd.DataFrame:
    file_path = RAW_DATA_DIR / f"{cell_type}.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"File {cell_type}.csv not found")
    
    def safe_float(x):
        s = str(x).replace('%', '').replace(',', '.').strip()
        if s == '' or s.lower() == 'nan':
            return float('nan')
        return float(s)

    df = pd.read_csv(
        file_path,
        decimal=',',
        thousands='.',
        converters={col: safe_float for col in FEATURES + [TARGET]}
    )
    
    missing = [col for col in FEATURES + [TARGET] if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    return df
