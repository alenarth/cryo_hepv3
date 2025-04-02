import pandas as pd
import joblib
from config import Config

class CryoPredictor:
    def __init__(self, cell_type: str):
        self.cell_type = cell_type
        self.model = self.load_model()
        
    def load_model(self):
        model_path = Config.MODELS_DIR / f"xgboost_{self.cell_type}.pkl"
        if not model_path.exists():
            raise FileNotFoundError(f"Modelo para {self.cell_type} não encontrado")
        return joblib.load(model_path)
    
    def validate_inputs(self, concentrations: dict) -> bool:
        """Valida entradas conforme regras"""
        for key, value in concentrations.items():
            if value % Config.ALLOWED_STEP != 0:
                return False
            if not (Config.MIN_CONC <= value <= Config.MAX_CONC):
                return False
        return True
    
    def predict(self, concentrations: dict) -> float:
        """Faz predição validada"""
        if not self.validate_inputs(concentrations):
            raise ValueError("Concentrações inválidas")
            
        input_data = pd.DataFrame([concentrations], columns=Config.FEATURES)
        predicted_drop = self.model.predict(input_data)[0]
        return max(0, min(100, round(100 - predicted_drop, 1)))