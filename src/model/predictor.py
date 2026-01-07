import pandas as pd
import joblib
from config import Config

class CryoPredictor:
    def __init__(self, cell_type: str) -> None:
        """Inicializa o preditor para o tipo celular."""
        self.cell_type = cell_type
        self.model = self.load_model()

    def load_model(self) -> object:
        """Carrega o modelo do disco."""
        model_path = Config.MODELS_DIR / f"xgboost_{self.cell_type}.pkl"
        if not model_path.exists():
            raise FileNotFoundError(f"Modelo para {self.cell_type} não encontrado")
        return joblib.load(model_path)

    def validate_inputs(self, concentrations: dict) -> bool:
        """Valida que as concentrações estejam dentro do passo e intervalo permitidos."""
        for key, value in concentrations.items():
            # Fazer checagem robusta para valores float
            if abs((value / Config.ALLOWED_STEP) - round(value / Config.ALLOWED_STEP)) > 1e-8:
                return False
            if not (Config.MIN_CONC <= value <= Config.MAX_CONC):
                return False
        return True

    def predict(self, concentrations: dict) -> float:
        """Realiza predição validada e retorna a viabilidade (0-100)."""
        if not self.validate_inputs(concentrations):
            raise ValueError("Concentrações inválidas")

        input_data = pd.DataFrame([concentrations], columns=Config.FEATURES)
        predicted_drop = self.model.predict(input_data)[0]
        return float(round(max(0.0, min(100.0, 100 - predicted_drop)), 1))