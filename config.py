import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()

class Config:
    CELL_TYPES = ['hepg2', 'rat', 'mice']
    
    # Diretórios
    RAW_DATA_DIR = BASE_DIR / "data" / "raw"
    PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
    MODELS_DIR = BASE_DIR / "models"
    GRAPHS_DIR = BASE_DIR / "static" / "graphs"
    
    # Colunas do dataset (corrigido espaços)
    FEATURES = ['% DMSO', 'TREHALOSE']
    TARGET = '% QUEDA DA VIABILIDADE' 
    
    # Configurações de validação
    ALLOWED_STEP = 5
    MIN_CONC = 0
    MAX_CONC = 100

    # Criar diretórios
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)
    # os.makedirs(GRAPHS_DIR, exist_ok=True)  # Não necessário, pois static/graphs já existe