import pandas as pd
import joblib
from config import Config

class CryoPredictor:
    def __init__(self, cell_type: str) -> None:
        """
        Inicializa o preditor para o tipo celular.
        Args:
            cell_type (str): Nome do tipo celular.
        """
        self.cell_type = cell_type
        self.model = self.load_model()
        
    def load_model(self) -> object:
        """
        Carrega o modelo do disco.
        Returns:
            object: Modelo carregado.
        Raises:
            FileNotFoundError: Se o modelo não existir.
        """
        model_path = Config.MODELS_DIR / f"xgboost_{self.cell_type}.pkl"
        if not model_path.exists():
            raise FileNotFoundError(f"Modelo para {self.cell_type} não encontrado")
        return joblib.load(model_path)
    
    def validate_inputs(self, concentrations: dict) -> bool:
        """
        Valida as concentrações de entrada.
        Args:
            concentrations (dict): Dicionário de concentrações.
        Returns:
            bool: True se válido, False caso contrário.
        """
        """Valida entradas conforme regras"""
        for key, value in concentrations.items():
            if value % Config.ALLOWED_STEP != 0:
                return False
            if not (Config.MIN_CONC <= value <= Config.MAX_CONC):
                return False
        return True
    
    def predict(self, concentrations: dict) -> float:
        """
        Realiza predição validada.
        Args:
            concentrations (dict): Dicionário de concentrações.
        Returns:
            float: Valor previsto.
        Raises:
            ValueError: Se as concentrações forem inválidas.
        """
        """Faz predição validada"""
        if not self.validate_inputs(concentrations):
            raise ValueError("Concentrações inválidas")
            
        input_data = pd.DataFrame([concentrations], columns=Config.FEATURES)
        predicted_drop = self.model.predict(input_data)[0]
        return max(0, min(100, round(100 - predicted_drop, 1)))