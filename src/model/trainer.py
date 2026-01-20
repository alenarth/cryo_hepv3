from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
import joblib
import pandas as pd
import logging
from pathlib import Path
from src.data.loader import load_raw_data

logger = logging.getLogger(__name__)

# Constants
BASE_DIR = Path(__file__).parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
FEATURES = ['% DMSO', 'TREHALOSE']
TARGET = '% QUEDA DA VIABILIDADE'
MIN_CONC = 0
MAX_CONC = 100

class CryoModelTrainer:
    def __init__(self, cell_type: str, variant: str = 'default') -> None:
        """Inicializa o treinador para o tipo celular e variante."""
        self.cell_type = cell_type
        self.variant = variant
        self.model = XGBRegressor(
            objective='reg:squarederror',
            n_estimators=500,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.9,
            colsample_bytree=0.8
        )

    def _filter_variant(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filtra o DataFrame de acordo com a variante desejada."""
        dm_col = FEATURES[0]
        tr_col = FEATURES[1]
        if self.variant == 'dmso_only':
            return df[(df[dm_col] > 0) & (df[tr_col] == 0)]
        if self.variant == 'trehalose_only':
            return df[(df[tr_col] > 0) & (df[dm_col] == 0)]
        if self.variant == 'both':
            return df[(df[dm_col] > 0) & (df[tr_col] > 0)]
        return df

    def prepare_data(self, df: pd.DataFrame):
        """Prepara e valida os dados para treinamento."""
        for col in FEATURES + [TARGET]:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df = df.dropna(subset=FEATURES + [TARGET])
        
        # Excluir controle contaminado: onde ambas as colunas são 0
        dm_col = FEATURES[0]
        tr_col = FEATURES[1]
        df = df[~((df[dm_col] == 0) & (df[tr_col] == 0))]
        
        # Para modelo DEFAULT: usar apenas dados "puros" (um ou outro crioprotetor)
        if self.variant == 'default':
            df = df[((df[dm_col] > 0) & (df[tr_col] == 0)) | ((df[dm_col] == 0) & (df[tr_col] > 0))]
        
        mask_low = (df[FEATURES] >= MIN_CONC).all(axis=1)
        mask_high = (df[FEATURES] <= MAX_CONC).all(axis=1)
        df = df[mask_low & mask_high]
        df = self._filter_variant(df)

        return train_test_split(
            df[FEATURES],
            df[TARGET],
            test_size=0.2,
            random_state=42
        )
    
    def train_and_save(self):
        """Executa treinamento e salva o modelo."""
        df = load_raw_data(self.cell_type)
        X_train, X_test, y_train, y_test = self.prepare_data(df)

        if len(X_train) < 10:
            raise ValueError("Dados insuficientes para treinamento")

        self.model.fit(X_train, y_train)
        suffix = '' if self.variant == 'default' else f"_{self.variant}"
        model_path = MODELS_DIR / f"xgboost_{self.cell_type}{suffix}.pkl"
        joblib.dump(self.model, model_path)

        logger.info(f"Modelo ({self.variant}) salvo em {model_path}")
        return X_test, y_test