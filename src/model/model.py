import pandas as pd
import joblib
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from config import Config

# --- DATA ---
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
    missing = [col for col in Config.FEATURES + [Config.TARGET] if col not in df.columns]
    if missing:
        raise ValueError(f"Colunas faltando: {missing}")
    return df

# --- MODEL ---
class CryoPredictor:
    def __init__(self, cell_type: str) -> None:
        self.cell_type = cell_type
        self.model = self.load_model()
    def load_model(self) -> object:
        model_path = Config.MODELS_DIR / f"xgboost_{self.cell_type}.pkl"
        if not model_path.exists():
            raise FileNotFoundError(f"Modelo para {self.cell_type} não encontrado")
        return joblib.load(model_path)
    def validate_inputs(self, concentrations: dict) -> bool:
        for key, value in concentrations.items():
            if value % Config.ALLOWED_STEP != 0:
                return False
            if not (Config.MIN_CONC <= value <= Config.MAX_CONC):
                return False
        return True
    def predict(self, concentrations: dict) -> float:
        if not self.validate_inputs(concentrations):
            raise ValueError("Concentrações inválidas")
        input_data = pd.DataFrame([concentrations], columns=Config.FEATURES)
        return self.model.predict(input_data)[0]

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
        try:
            df = load_raw_data(self.cell_type)
            X_train, X_test, y_train, y_test = self.prepare_data(df)
            self.model.fit(X_train, y_train)
            joblib.dump(self.model, Config.MODELS_DIR / f"xgboost_{self.cell_type}.pkl")
        except Exception as e:
            raise Exception(f"Erro no treinamento: {str(e)}")
