import pandas as pd
from pathlib import Path
from config import Config

def load_raw_data(cell_type: str) -> pd.DataFrame:
    """Carrega dados com validação rigorosa"""
    file_path = Config.RAW_DATA_DIR / f"{cell_type}.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo {cell_type}.csv não encontrado")
    
    df = pd.read_csv(
        file_path,
        decimal=',',
        thousands='.',
        converters={
            col: lambda x: float(str(x).replace('%','').replace(',','.').strip())
            for col in Config.FEATURES + [Config.TARGET]
        }
    )
    
    # Validação de colunas
    missing = [col for col in Config.FEATURES + [Config.TARGET] if col not in df.columns]
    if missing:
        raise ValueError(f"Colunas faltando: {missing}")
        
    return df