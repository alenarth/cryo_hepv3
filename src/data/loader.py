import pandas as pd
from config import Config

def load_raw_data(cell_type: str) -> pd.DataFrame:
    """
    Carrega dados brutos do tipo celular informado.
    Args:
        cell_type (str): Nome do tipo celular.
    Returns:
        pd.DataFrame: DataFrame validado com os dados.
    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ValueError: Se colunas obrigatórias estiverem faltando.
    """
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