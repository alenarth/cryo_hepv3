"""
Centralização de constantes do projeto Cryo Hepatocytes.

Este módulo contém todas as constantes, ranges e configurações que são
usadas em múltiplos lugares da aplicação, evitando duplicação e facilitando
manutenção.
"""

from pathlib import Path

# ========== Tipos Celulares ==========
VALID_CELL_TYPES = {'hepg2', 'mice', 'rat'}
CELL_TYPES_LIST = sorted(list(VALID_CELL_TYPES))

# ========== Crioprotetores ==========
VALID_CRYOPROTECTORS = {'DMSO', 'TREHALOSE', 'BOTH'}

# Mapeamento: nome do crioprotetor → coluna no CSV/modelo
FEATURE_MAP = {
    'DMSO': '% DMSO',
    'TREHALOSE': 'TREHALOSE'
}

# Nomes das features no modelo (ordem importa)
MODEL_FEATURES = list(FEATURE_MAP.values())  # ['% DMSO', 'TREHALOSE']

# ========== Ranges de Concentração ==========
CONCENTRATION_STEP = 5
CONCENTRATION_MIN = 0
CONCENTRATION_MAX = 100

# Gera ranges dinamicamente
CONCENTRATION_RANGES = {
    'DMSO': list(range(CONCENTRATION_MIN, CONCENTRATION_MAX + 1, CONCENTRATION_STEP)),
    'TREHALOSE': list(range(CONCENTRATION_MIN, CONCENTRATION_MAX + 1, CONCENTRATION_STEP)),
    'BOTH': list(range(CONCENTRATION_MIN, CONCENTRATION_MAX + 1, CONCENTRATION_STEP))
}

# ========== Variantes de Modelo ==========
MODEL_VARIANTS = {'default', 'dmso_only', 'trehalose_only', 'both'}
VARIANT_MAPPING = {
    'DMSO': 'dmso_only',
    'TREHALOSE': 'trehalose_only',
    'BOTH': 'both'
}

# ========== Limites de API ==========
RATE_LIMIT_PREDICT = "30/minute"
RATE_LIMIT_MIXTURE = "30/minute"

# ========== Limites de Validação ==========
MIN_MIXTURE_COMPONENTS = 2
MAX_MIXTURE_COMPONENTS = 5

# ========== Valores de Viabilidade ==========
VIABILITY_MIN = 0.0
VIABILITY_MAX = 100.0
VIABILITY_DECIMAL_PLACES = 1

# ========== Tolerância de Float ==========
FLOAT_TOLERANCE = 1e-6
