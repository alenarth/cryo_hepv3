import os
from config import Config
import joblib
import pandas as pd
import numpy as np
from src.visualization.plotter import generate_model_analysis

def main():
    for cell_type in Config.CELL_TYPES:
        print(f"Gerando gráficos para: {cell_type}")
        model_path = os.path.join(Config.MODELS_DIR, f"xgboost_{cell_type}.pkl")
        data_path = os.path.join(Config.RAW_DATA_DIR, f"{cell_type}.csv")
        if not os.path.exists(model_path) or not os.path.exists(data_path):
            print(f"Modelo ou dados não encontrados para {cell_type}")
            continue
        model = joblib.load(model_path)
        df = pd.read_csv(data_path)
        # Converte todas as colunas de entrada para float
        for col in Config.FEATURES + [Config.TARGET]:
            df[col] = df[col].apply(lambda x: float(str(x).replace('%','').replace(',','.').strip()) if pd.notnull(x) else np.nan)
        # Remove linhas com NaN nas features ou target
        df = df.dropna(subset=Config.FEATURES + [Config.TARGET])
        if df.shape[0] == 0:
            print(f"Nenhum dado válido para {cell_type} após remoção de NaN. Pulando...")
            continue
        X = df[Config.FEATURES].astype(float)
        y = df[Config.TARGET].astype(float)
        generate_model_analysis(model, X, y, cell_type)

if __name__ == "__main__":
    main()
