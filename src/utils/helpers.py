"""
Módulo de utilidades para processamento de dados e validações.

Contém funções compartilhadas para parsing, validação e manipulação
de dados usadas em múltiplos pontos da aplicação.
"""

import logging
import pandas as pd
from pathlib import Path
from src.constants import (
    FEATURE_MAP, MODEL_FEATURES, VALID_CELL_TYPES, VALID_CRYOPROTECTORS,
    CONCENTRATION_RANGES, VIABILITY_MIN, VIABILITY_MAX, VIABILITY_DECIMAL_PLACES,
    FLOAT_TOLERANCE
)

logger = logging.getLogger(__name__)

# Definir RAW_DATA_DIR
RAW_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"


# ========== PARSING & TYPE CONVERSION ==========

def parse_percent_value(value: object) -> float | None:
    """
    Converte valores como '10%', '10,5%', '10.5' para float.
    
    Args:
        value: Valor a ser convertido (pode ser str, int, float, None)
        
    Returns:
        float: Valor numérico, ou None se não puder ser interpretado
        
    Examples:
        >>> parse_percent_value('10,5%')
        10.5
        >>> parse_percent_value('10')
        10.0
        >>> parse_percent_value('NA')
        None
    """
    if value is None:
        return None
    
    try:
        s = str(value).strip()
        if s == '' or s.lower() in {'x', 'na', 'nan', 'none'}:
            return None
        
        # Remove símbolo de porcentagem
        s = s.replace('%', '').replace('"', '').strip()
        # Converte vírgula decimal em ponto
        s = s.replace(',', '.')
        return float(s)
    except Exception as e:
        logger.debug(f"Falha ao fazer parse de '{value}': {e}")
        return None


# ========== FEATURE BUILDING ==========

def build_feature_row(cryoprotector: str, concentration: float) -> dict:
    """
    Constrói um vetor de features para o modelo XGBoost.
    
    Cria um dicionário com as colunas esperadas pelo modelo, setando
    o crioprotetor especificado e zerando os demais.
    
    Args:
        cryoprotector: Um de {'DMSO', 'TREHALOSE', 'BOTH'}
        concentration: Valor de concentração (0-100)
        
    Returns:
        dict: Mapeamento {coluna_modelo: valor_concentração}
        
    Examples:
        >>> build_feature_row('DMSO', 50)
        {'% DMSO': 50.0, 'TREHALOSE': 0.0}
        
        >>> build_feature_row('BOTH', 30)
        {'% DMSO': 30.0, 'TREHALOSE': 30.0}
    """
    cryo = cryoprotector.upper()
    row = {col: 0.0 for col in MODEL_FEATURES}
    
    if cryo == 'BOTH':
        # BOTH: aplica mesma concentração em ambas as colunas
        for col in MODEL_FEATURES:
            row[col] = float(concentration)
    elif cryo in FEATURE_MAP:
        # DMSO ou TREHALOSE: coloca valor apenas na coluna correspondente
        row[FEATURE_MAP[cryo]] = float(concentration)
    else:
        logger.warning(f"Crioprotetor desconhecido: {cryo}")
    
    return row


# ========== VIABILITY PROCESSING ==========

def clamp_viability(value: float) -> float:
    """
    Normaliza um valor de viabilidade ao intervalo [0, 100].
    
    Args:
        value: Valor bruto de viabilidade
        
    Returns:
        float: Valor normalizado e arredondado a 1 casa decimal
        
    Examples:
        >>> clamp_viability(150)
        100.0
        >>> clamp_viability(-5)
        0.0
        >>> clamp_viability(50.567)
        50.6
    """
    clamped = max(VIABILITY_MIN, min(VIABILITY_MAX, value))
    return float(round(clamped, VIABILITY_DECIMAL_PLACES))


# ========== VALIDATION ==========

def validate_cell_type(cell_type: str) -> tuple[bool, str | None]:
    """
    Valida se o tipo celular é permitido.
    
    Args:
        cell_type: Tipo celular a validar
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(cell_type, str):
        return False, "Tipo celular deve ser texto"
    
    cell_type_lower = cell_type.lower()
    if cell_type_lower not in VALID_CELL_TYPES:
        return False, f"Tipo celular inválido: {cell_type}. Válidos: {VALID_CELL_TYPES}"
    
    return True, None


def validate_cryoprotector(cryoprotector: str) -> tuple[bool, str | None]:
    """
    Valida se o crioprotetor é permitido.
    
    Args:
        cryoprotector: Crioprotetor a validar
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(cryoprotector, str):
        return False, "Crioprotetor deve ser texto"
    
    cryo_upper = cryoprotector.upper()
    if cryo_upper not in VALID_CRYOPROTECTORS:
        return False, f"Crioprotetor inválido: {cryoprotector}. Válidos: {VALID_CRYOPROTECTORS}"
    
    return True, None


def validate_concentration(concentration: float, cryoprotector: str) -> tuple[bool, str | None]:
    """
    Valida se a concentração é válida para o crioprotetor.
    
    Args:
        concentration: Valor de concentração
        cryoprotector: Tipo de crioprotetor
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        conc_float = float(concentration)
    except (TypeError, ValueError):
        return False, "Concentração deve ser numérica"
    
    allowed = CONCENTRATION_RANGES.get(cryoprotector.upper(), [])
    if not allowed:
        return False, f"Crioprotetor inválido: {cryoprotector}"
    
    # Converte allowed para float se necessário e verifica tolerância
    allowed_floats = [float(c) for c in allowed]
    if not any(abs(conc_float - c) < max(FLOAT_TOLERANCE, 0.1) for c in allowed_floats):
        return False, f"Concentração {conc_float} não permitida. Valores: {allowed}"
    
    return True, None


def validate_input(cell_type: str, cryoprotector: str) -> list[str]:
    """
    Valida combinação de tipo celular e crioprotetor.
    
    Args:
        cell_type: Tipo celular
        cryoprotector: Crioprotetor
        
    Returns:
        list: Lista de mensagens de erro (vazia se válido)
    """
    errors = []
    
    is_valid, error = validate_cell_type(cell_type)
    if not is_valid:
        errors.append(error)
    
    is_valid, error = validate_cryoprotector(cryoprotector)
    if not is_valid:
        errors.append(error)
    
    return errors


# ========== DATA EXTRACTION ==========

def get_available_both_combinations(cell_type: str) -> list[tuple[float, float]]:
    """
    Extrai pares únicos (DMSO, TREHALOSE) encontrados no CSV raw.
    
    Retorna apenas pares onde ambos os valores são > 0.
    
    Args:
        cell_type: Tipo celular
        
    Returns:
        list: Lista de tuplas (dmso_value, trehalose_value), ou [] se erro
        
    Examples:
        >>> get_available_both_combinations('hepg2')
        [(5.0, 5.0), (10.0, 10.0), (10.0, 5.0), ...]
    """
    try:
        path = RAW_DATA_DIR / f"{cell_type}.csv"
        if not path.exists():
            logger.warning(f"Arquivo não encontrado: {path}")
            return []
        
        df = pd.read_csv(path, dtype=str, engine='python')
        dmso_col = FEATURE_MAP['DMSO']
        tre_col = FEATURE_MAP['TREHALOSE']
        
        if dmso_col not in df.columns or tre_col not in df.columns:
            logger.warning(f"Colunas esperadas não encontradas em {path}")
            return []
        
        dmso_vals = df[dmso_col].map(parse_percent_value)
        tre_vals = df[tre_col].map(parse_percent_value)
        
        pairs = pd.DataFrame({dmso_col: dmso_vals, tre_col: tre_vals}).dropna()
        # Filtra pares onde ambos > 0
        pairs = pairs[(pairs[dmso_col] > 0) & (pairs[tre_col] > 0)]
        pairs = pairs.drop_duplicates().sort_values(by=[dmso_col, tre_col])
        
        return [(float(r[dmso_col]), float(r[tre_col])) for _, r in pairs.iterrows()]
    except Exception as e:
        logger.error(f"Erro ao extrair combinações para {cell_type}: {e}")
        return []


def get_min_nonzero_feature(cell_type: str, feature_col: str) -> float | None:
    """
    Retorna o menor valor > 0 encontrado em uma coluna do CSV raw.
    
    Args:
        cell_type: Tipo celular
        feature_col: Nome da coluna no CSV
        
    Returns:
        float: Menor valor > 0, ou None se não encontrado
        
    Examples:
        >>> get_min_nonzero_feature('hepg2', '% DMSO')
        5.0
    """
    try:
        path = RAW_DATA_DIR / f"{cell_type}.csv"
        if not path.exists():
            logger.debug(f"Arquivo não encontrado: {path}")
            return None
        
        df = pd.read_csv(path, dtype=str, engine='python')
        if feature_col not in df.columns:
            logger.debug(f"Coluna {feature_col} não encontrada em {path}")
            return None
        
        vals = df[feature_col].map(parse_percent_value).dropna()
        vals = vals[vals > 0]
        
        if vals.empty:
            return None
        
        return float(vals.min())
    except Exception as e:
        logger.error(f"Erro ao obter min_nonzero para {feature_col} em {cell_type}: {e}")
        return None
