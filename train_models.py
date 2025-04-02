from src.model.trainer import CryoModelTrainer
from src.visualization.plotter import generate_model_analysis
from config import Config
import joblib
import os

def train_all_models():
    """Treina e salva modelos para todos os tipos celulares com análise completa"""
    try:
        # Verificar arquivos necessários
        required_files = ['hepg2.csv', 'rat.csv', 'mice.csv']
        for file in required_files:
            if not (Config.RAW_DATA_DIR / file).exists():
                raise FileNotFoundError(f"Arquivo {file} não encontrado")

        # Treinar modelos
        for cell_type in Config.CELL_TYPES:
            print(f"\n{'='*40}")
            print(f"Treinando modelo para: {cell_type.upper()}")
            print(f"{'='*40}")
            
            try:
                # Treinar e salvar modelo
                trainer = CryoModelTrainer(cell_type)
                X_test, y_test = trainer.train_and_save()
                
                if X_test is None:
                    print(f"Falha no treinamento para {cell_type}")
                    continue
                
                # Carregar modelo para análise
                model_path = Config.MODELS_DIR / f"xgboost_{cell_type}.pkl"
                model = joblib.load(model_path)
                
                # Gerar análise completa
                print(f"Gerando gráficos de análise para {cell_type}...")
                generate_model_analysis(model, X_test, y_test, cell_type)
                
                print(f"\n[{cell_type.upper()}] Treinamento e análise concluídos!")

            except Exception as e:
                print(f"Erro em {cell_type}: {str(e)}")
                continue
            try:
                metrics_path = generate_model_analysis(model, X_test, y_test, cell_type)
                print(f"Métricas salvas em: {metrics_path}")
            except Exception as e:
                print(f"Erro ao gerar métricas: {str(e)}")
                continue
        print("\nProcesso de treinamento finalizado!")

    except Exception as e:
        print(f"\nERRO GLOBAL: {str(e)}")
        raise

if __name__ == "__main__":
    # Garantir diretórios existem
    Config.MODELS_DIR.mkdir(exist_ok=True)
    Config.GRAPHS_DIR.mkdir(exist_ok=True)
    
    print("Iniciando treinamento de modelos...")
    train_all_models()