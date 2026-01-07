import pandas as pd
import joblib
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from config import Config

# --- DATA ---
from src.data.loader import load_raw_data


# --- MODEL ---
# Predictor implementation moved to `src.model.predictor.CryoPredictor` to avoid duplication.

class CryoModelTrainer:
    def __init__(self, cell_type: str) -> None:
        self.cell_type = cell_type
        self.model = XGBRegressor(
            objective='reg:squarederror',
            n_estimators=500,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.9,
            colsample_bytree=0.8
        )
    def prepare_data(self, df: pd.DataFrame) -> tuple:
        for col in Config.FEATURES + [Config.TARGET]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=Config.FEATURES + [Config.TARGET])
        df = df[(df[Config.FEATURES] >= Config.MIN_CONC).all(axis=1) & \
               (df[Config.FEATURES] <= Config.MAX_CONC).all(axis=1)]
        return train_test_split(
            df[Config.FEATURES],
            df[Config.TARGET],
            test_size=0.2,
            random_state=42
        )
    def train_and_save(self) -> None:
        df = load_raw_data(self.cell_type)
        X_train, X_test, y_train, y_test = self.prepare_data(df)
        self.model.fit(X_train, y_train)
        joblib.dump(self.model, Config.MODELS_DIR / f"xgboost_{self.cell_type}.pkl")
