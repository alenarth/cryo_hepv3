import logging
from pathlib import Path
from src.model.trainer import CryoModelTrainer
from src.visualization.plotter import generate_model_analysis
import joblib

logger = logging.getLogger(__name__)

# Constants
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
CELL_TYPES = ['hepg2', 'rat', 'mice']

def train_all_models():
    """Treina e salva modelos para todos os tipos celulares."""
    try:
        # Verificar arquivos necessários
        required_files = ['hepg2.csv', 'rat.csv', 'mice.csv']
        for file in required_files:
            if not (RAW_DATA_DIR / file).exists():
                raise FileNotFoundError(f"Arquivo {file} não encontrado")

        variants = ['default', 'dmso_only', 'trehalose_only', 'both']

        # Treinar modelos
        for cell_type in CELL_TYPES:
            logger.info("%s", "="*40)
            logger.info("Treinando modelos para: %s", cell_type.upper())
            logger.info("%s", "="*40)

            for variant in variants:
                try:
                    logger.info("Treinando variante: %s", variant)
                    trainer = CryoModelTrainer(cell_type, variant=variant)
                    X_test, y_test = trainer.train_and_save()

                    if X_test is None:
                        logger.error("Falha no treinamento para %s (variante %s)", cell_type, variant)
                        continue

                    # Carregar modelo para análise
                    suffix = '' if variant == 'default' else f"_{variant}"
                    model_path = MODELS_DIR / f"xgboost_{cell_type}{suffix}.pkl"
                    model = joblib.load(model_path)

                    # Gerar análise
                    logger.info("Gerando gráficos de análise para %s (%s)...", cell_type, variant)
                    metrics_path = generate_model_analysis(model, X_test, y_test, f"{cell_type}_{variant}")

                    logger.info("[%s - %s] Treinamento e análise concluídos!", cell_type.upper(), variant)
                    logger.info("Métricas salvas em: %s", metrics_path)

                except ValueError as ve:
                    logger.warning("Dados insuficientes para %s (%s): %s", cell_type, variant, ve)
                    continue
                except Exception as e:
                    logger.exception("Erro em %s (%s): %s", cell_type, variant, str(e))
                    continue

            logger.info("\nProcesso de treinamento finalizado para %s!", cell_type)

    except Exception as e:
        logger.exception("ERRO GLOBAL: %s", str(e))
        raise

if __name__ == "__main__":
    # Garantir diretórios existem
    MODELS_DIR.mkdir(exist_ok=True, parents=True)

    logger.info("Iniciando treinamento de modelos...")
    train_all_models()