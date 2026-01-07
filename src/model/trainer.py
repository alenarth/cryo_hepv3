from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
import joblib
import pandas as pd
import logging
from config import Config
from src.data.loader import load_raw_data

logger = logging.getLogger(__name__)

class CryoModelTrainer:
    def __init__(self, cell_type: str) -> None:
        """
        Inicializa o treinador para o tipo celular.
        Args:
            cell_type (str): Nome do tipo celular.
        """
        self.cell_type = cell_type
        self.model = XGBRegressor(
            objective='reg:squarederror',
            n_estimators=500,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.9,
            colsample_bytree=0.8
        )

    def prepare_data(self, df: pd.DataFrame):
        """Prepara e valida os dados para treinamento.

        Converte colunas para numérico, remove linhas com NA nas features/target
        e filtra por limites configurados.
        """
        # Converter e filtrar
        for col in Config.FEATURES + [Config.TARGET]:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df = df.dropna(subset=Config.FEATURES + [Config.TARGET])
        mask_low = (df[Config.FEATURES] >= Config.MIN_CONC).all(axis=1)
        mask_high = (df[Config.FEATURES] <= Config.MAX_CONC).all(axis=1)
        df = df[mask_low & mask_high]

        return train_test_split(
            df[Config.FEATURES],
            df[Config.TARGET],
            test_size=0.2,
            random_state=42
        )
    
    def train_and_save(self):
        """Executa treinamento e salva o modelo. Retorna (X_test, y_test)."""
        df = load_raw_data(self.cell_type)
        X_train, X_test, y_train, y_test = self.prepare_data(df)

        if len(X_train) < 10:
            raise ValueError("Dados insuficientes para treinamento")

        self.model.fit(X_train, y_train)
        model_path = Config.MODELS_DIR / f"xgboost_{self.cell_type}.pkl"
        joblib.dump(self.model, model_path)

        logger.info(f"Modelo salvo em {model_path}")
        return X_test, y_test