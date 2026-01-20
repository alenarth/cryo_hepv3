"""
Aplicação Flask principal para o sistema de predição de viabilidade celular.

Oferece uma API REST para predição de viabilidade de hepatócitos criopreservados
e uma interface web interativa.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import joblib
import pandas as pd
from pathlib import Path
from functools import lru_cache
import logging
import os

from src.constants import (
    VALID_CELL_TYPES, VALID_CRYOPROTECTORS, FEATURE_MAP, MODEL_FEATURES
)
from src.utils.helpers import (
    build_feature_row, clamp_viability,
    validate_input, validate_cell_type, validate_cryoprotector, validate_concentration,
    get_available_both_combinations, get_min_nonzero_feature
)

# Configuração
BASE_DIR = Path(__file__).parent.resolve()
CELL_TYPES = ['hepg2', 'rat', 'mice']
MODELS_DIR = Path(os.getenv('MODELS_DIR', BASE_DIR / "models"))
GRAPHS_DIR = Path(os.getenv('GRAPHS_DIR', BASE_DIR / "static" / "graphs"))
CONCENTRATION_RANGES = {
    'DMSO': list(range(0, 101, 5)),
    'TREHALOSE': list(range(0, 101, 5))
}

app = Flask(__name__)
app.config['DEBUG'] = True
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


@app.route('/predict-mixture', methods=['POST'])
def predict_mixture():
    """Prediz viabilidade para mistura de crioprotetores (2-5)."""
    try:
        data = request.json or {}
        cell_type = str(data.get('cell_type', '')).lower()
        mixture = data.get('mixture', [])
        
        # Validação
        if cell_type not in VALID_CELL_TYPES:
            return jsonify({'error': f'Tipo celular inválido: {cell_type}'}), 400
        if not (2 <= len(mixture) <= 5):
            return jsonify({'error': 'Mistura deve conter 2-5 crioprotetores'}), 400
        
        # Preparar features
        input_dict = {col: 0.0 for col in MODEL_FEATURES}
        for item in mixture:
            cp = str(item.get('cryoprotector', '')).upper()
            if cp not in FEATURE_MAP:
                return jsonify({'error': f'Crioprotetor inválido: {cp}'}), 400
            input_dict[FEATURE_MAP[cp]] = float(item.get('concentration', 0))
        
        # Determinar variante
        has_dmso = input_dict.get(FEATURE_MAP['DMSO'], 0) > 0
        has_tre = input_dict.get(FEATURE_MAP['TREHALOSE'], 0) > 0
        variant = 'both' if (has_dmso and has_tre) else ('dmso_only' if has_dmso else 'trehalose_only')
        
        model = try_load_model(cell_type, variant=variant)
        if not model:
            return jsonify({'error': f'Modelo não encontrado: {cell_type}'}), 404
        
        pred = 100 - model.predict(pd.DataFrame([input_dict]))[0]
        return jsonify({'viability': clamp_viability(pred), 'model_variant': variant})
    except Exception as e:
        logger.error(f"Erro /predict-mixture: {e}")
        return jsonify({'error': 'Erro ao prever mistura'}), 500

# Cache simples para modelos
@lru_cache(maxsize=32)
def get_model(cell_type: str, variant: str | None = None):
    """Carrega o modelo XGBoost para o tipo celular dado.
    
    Se `variant` for especificado, tenta carregar o modelo variant primeiro.
    Se não encontrado, volta ao modelo padrão.
    
    Args:
        cell_type: Um de {'hepg2', 'mice', 'rat'}
        variant: Um de {'default', 'dmso_only', 'trehalose_only', 'both'}, ou None
        
    Returns:
        Modelo joblib carregado
        
    Raises:
        FileNotFoundError: Se nenhuma variante for encontrada
        RuntimeError: Se houver erro ao carregar
    """
    cell_type = str(cell_type).lower()
    if cell_type not in VALID_CELL_TYPES:
        raise FileNotFoundError(f"Tipo celular inválido: {cell_type}")
    
    # Tenta carregar variante específica se pedida
    if variant:
        suffix = f"_{variant}"
        model_path = MODELS_DIR / f"xgboost_{cell_type}{suffix}.pkl"
        if model_path.exists():
            try:
                return joblib.load(model_path)
            except Exception as e:
                logger.error(f"Erro ao carregar modelo {model_path}: {e}")
                raise RuntimeError(f"Falha ao carregar modelo: {e}") from e
    
    # Fallback: modelo padrão
    model_path = MODELS_DIR / f"xgboost_{cell_type}.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Modelo não encontrado: {model_path}")
    
    try:
        return joblib.load(model_path)
    except Exception as e:
        logger.error(f"Erro ao carregar modelo {model_path}: {e}")
        raise RuntimeError(f"Falha ao carregar modelo: {e}") from e


def try_load_model(cell_type: str, variant: str | None = None):
    """Tenta carregar modelo; retorna None em caso de erro."""
    try:
        return get_model(cell_type, variant=variant)
    except FileNotFoundError as fe:
        logger.warning(str(fe))
        return None
    except Exception as e:
        logger.error(f"Erro ao carregar modelo: {e}")
        return None

@app.route('/')
def index() -> str:
    """Página inicial do sistema."""
    return render_template('index.html', 
        config={
            'CELL_TYPES': CELL_TYPES,
            'CRYOPROTECTORS': [('DMSO', 'DMSO'), ('TREHALOSE', 'Trehalose'), ('BOTH', 'Ambos (DMSO + Trehalose)')],
            'FEATURES': MODEL_FEATURES
        }
    )


@app.route('/developer')
def developer_area() -> str:
    """Área do desenvolvedor."""
    selected_cell_type = CELL_TYPES[0] if CELL_TYPES else ''
    return render_template('developer.html', 
        config={'CELL_TYPES': CELL_TYPES},
        selected_cell_type=selected_cell_type
    )


@app.route('/train-variants', methods=['POST'])
def train_variants_endpoint():
    """Inicia o treinamento dos modelos (todas as variantes) em thread separada.

    Nota: Esta rota apenas dispara o processo em background e retorna uma confirmação.
    """
    try:
        from threading import Thread
        from train_models import train_all_models

        def runner():
            try:
                train_all_models()
            except Exception as e:
                logging.exception('Erro no treinamento em background: %s', e)

        t = Thread(target=runner, daemon=True)
        t.start()
        return jsonify({'status': 'started'})
    except Exception as e:
        logging.error('Falha ao iniciar treinamento: %s', e)
        return jsonify({'error': 'Falha ao iniciar treinamento.'}), 500

@app.route('/predict', methods=['POST'])
def predict() -> object:
    """API: Retorna viabilidade para todas as concentrações de um crioprotetor.
    
    Retorna concentrações testadas, viabilidades correspondentes e
    a concentração ótima (maior viabilidade).
    """
    try:
        data = request.json
        
        # Validação
        cell_type = data.get('cell_type', '').lower()
        cryoprotector = data.get('cryoprotector', '').upper()
        
        errors = validate_input(cell_type, cryoprotector)
        if errors:
            return jsonify({'errors': errors}), 400
        
        # Carregar modelo
        model = try_load_model(cell_type)
        if model is None:
            return jsonify({'error': f"Modelo não encontrado para: {cell_type}"}), 404
        
        # Caso especial: BOTH (mistura com pares do dataset)
        if cryoprotector == 'BOTH':
            return _predict_both_from_dataset(model, cell_type)
        
        # Caso normal: DMSO ou TREHALOSE isolados
        return _predict_single_cryoprotector(model, cell_type, cryoprotector)
        
    except Exception as e:
        logger.error(f"Erro em /predict: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro interno ao prever viabilidade.'}), 500


def _predict_both_from_dataset(model, cell_type: str) -> object:
    """Prediz viabilidade para combinações DMSO+TREHALOSE encontradas no dataset."""
    pairs = get_available_both_combinations(cell_type)
    
    if not pairs:
        # Fallback: grade uniforme (ambos iguais, incrementos de 5)
        return _predict_both_fallback(model, cell_type)
    
    # Calcular viabilidade para cada par
    concentrations = [f"{int(d)}% + {int(t)}%" for d, t in pairs]
    viability = []
    
    for d, t in pairs:
        input_dict = {col: 0.0 for col in MODEL_FEATURES}
        input_dict[FEATURE_MAP['DMSO']] = float(d)
        input_dict[FEATURE_MAP['TREHALOSE']] = float(t)
        input_data = pd.DataFrame([input_dict])
        
        pred = 100 - model.predict(input_data)[0]
        viability.append(clamp_viability(pred))
    
    max_viab = max(viability)
    opt_index = viability.index(max_viab)
    
    logger.info(f"BOTH: {cell_type} ótimo={concentrations[opt_index]} ({max_viab})")
    
    return jsonify({
        'concentrations': concentrations,
        'viability': viability,
        'optimal': {
            'concentration': concentrations[opt_index],
            'value': float(max_viab)
        },
        'model_variant': 'both'
    })


def _predict_both_fallback(model, cell_type: str) -> object:
    """Fallback para BOTH: grid uniforme com incrementos de 5."""
    concentrations = CONCENTRATION_RANGES.get('BOTH', list(range(0, 101, 5)))
    viability = []
    
    for conc in concentrations:
        input_data = pd.DataFrame([build_feature_row('BOTH', conc)])
        pred = 100 - model.predict(input_data)[0]
        viability.append(clamp_viability(pred))
    
    max_viab = max(viability)
    opt_index = viability.index(max_viab)
    
    logger.info(f"BOTH (fallback): {cell_type} ótimo={concentrations[opt_index]} ({max_viab})")
    
    return jsonify({
        'concentrations': concentrations,
        'viability': viability,
        'optimal': {
            'concentration': concentrations[opt_index],
            'value': float(max_viab)
        },
        'model_variant': 'both (fallback)'
    })


def _predict_single_cryoprotector(model, cell_type: str, cryoprotector: str) -> object:
    """Prediz viabilidade para um crioprotetor isolado (DMSO ou TREHALOSE)."""
    # Selecionar modelo por variante se disponível
    variant_map = {'DMSO': 'dmso_only', 'TREHALOSE': 'trehalose_only'}
    preferred_variant = variant_map.get(cryoprotector)
    
    if preferred_variant:
        model = try_load_model(cell_type, variant=preferred_variant)
        if model is None:
            # Fallback para modelo padrão
            model = try_load_model(cell_type)
            if model is None:
                return jsonify({'error': f"Modelo não encontrado para: {cell_type}"}), 404
    
    # Preparar grade de concentrações
    base_concs = CONCENTRATION_RANGES.get(cryoprotector, list(range(0, 101, 5)))
    
    # Limitar ao intervalo observado nos dados se usando modelo específico
    if preferred_variant:
        feature_col = FEATURE_MAP[cryoprotector]
        min_obs = get_min_nonzero_feature(cell_type, feature_col)
        if min_obs is not None and min_obs > 0:
            base_concs = [c for c in base_concs if c >= min_obs]
            logger.info(f"{cryoprotector}: limitando a partir de {min_obs}")
    
    # Calcular viabilidade para cada concentração
    concentrations = base_concs
    viability = []
    
    for conc in concentrations:
        input_data = pd.DataFrame([build_feature_row(cryoprotector, conc)])
        pred = 100 - model.predict(input_data)[0]
        viability.append(clamp_viability(pred))
    
    max_viab = max(viability)
    opt_index = viability.index(max_viab)
    
    logger.info(f"{cryoprotector}: {cell_type} ótimo={concentrations[opt_index]} ({max_viab})")
    
    return jsonify({
        'concentrations': concentrations,
        'viability': viability,
        'optimal': {
            'concentration': concentrations[opt_index],
            'value': float(max_viab)
        },
        'model_variant': preferred_variant
    })



@app.route('/specific-predict', methods=['POST'])
def specific_predict() -> object:
    """API: Retorna viabilidade para uma concentração específica de um crioprotetor.
    
    Não funciona para BOTH (use a página de mistura para isso).
    """
    try:
        data = request.json
        
        cell_type = data.get('cell_type', '').lower()
        cryoprotector = data.get('cryoprotector', '').upper()
        concentration = data.get('concentration')
        
        errors = validate_input(cell_type, cryoprotector)
        
        # BOTH não é permitido aqui
        if cryoprotector == 'BOTH':
            errors.append('Para DMSO + TREHALOSE, use a página de Mistura.')
        
        # Validar concentração
        if concentration is not None:
            is_valid, error = validate_concentration(concentration, cryoprotector)
            if not is_valid:
                errors.append(error)
        else:
            errors.append('Concentração não informada.')
        
        if errors:
            return jsonify({'errors': errors}), 400
        
        # Carregar modelo
        variant_map = {'DMSO': 'dmso_only', 'TREHALOSE': 'trehalose_only'}
        preferred_variant = variant_map.get(cryoprotector)
        
        model = try_load_model(cell_type, variant=preferred_variant)
        if model is None:
            return jsonify({'error': f"Modelo não encontrado para: {cell_type}"}), 404
        
        # Fazer predição
        input_data = pd.DataFrame([build_feature_row(cryoprotector, concentration)])
        predicted_drop = model.predict(input_data)[0]
        viability = clamp_viability(100 - predicted_drop)
        
        logger.info(f"Específica: {cell_type}, {cryoprotector}, {concentration} -> {viability}")
        
        return jsonify({
            'viability': viability,
            'cell_type': cell_type.upper(),
            'cryoprotector': cryoprotector,
            'concentration': concentration
        })
    except Exception as e:
        logger.error(f"Erro em /specific-predict: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro interno ao prever viabilidade.'}), 500


# --- Endpoints para DMSO + TREHALOSE (pares) ---
@app.route('/available-both/<cell_type>')
def available_both(cell_type: str) -> object:
    """API: Retorna as combinações (DMSO, TREHALOSE) encontradas no dataset.
    
    Essas combinações aparecem no gráfico da opção 'DMSO + TREHALOSE'.
    """
    try:
        cell_type = str(cell_type).lower()
        
        is_valid, error = validate_cell_type(cell_type)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        pairs = get_available_both_combinations(cell_type)
        payload = [{'dmso': float(d), 'trehalose': float(t), 'label': f"{int(d)}% + {int(t)}%"} for d, t in pairs]
        
        return jsonify({'pairs': payload})
    except Exception as e:
        logger.error(f"Erro ao listar pares para {cell_type}: {e}", exc_info=True)
        return jsonify({'error': 'Erro interno ao listar combinações.'}), 500


@app.route('/predict-both', methods=['POST'])
def predict_both() -> object:
    """API: Prediz viabilidade para um par específico (DMSO, TREHALOSE).
    
    O par DEVE existir no dataset para garantir consistência com os dados.
    """
    try:
        data = request.json or {}
        cell_type = str(data.get('cell_type', '')).lower()
        
        try:
            dmso = float(data.get('dmso'))
            tre = float(data.get('trehalose'))
        except Exception:
            return jsonify({'errors': ['DMSO e TREHALOSE devem ser numéricos.']}), 400
        
        is_valid, error = validate_cell_type(cell_type)
        if not is_valid:
            return jsonify({'errors': [error]}), 400
        
        pairs = get_available_both_combinations(cell_type)
        if not pairs:
            return jsonify({'errors': ['Nenhuma combinação disponível neste dataset.']}), 400
        
        # Verificar se o par existe
        pair_exists = any(abs(dmso - d) < FLOAT_TOLERANCE and abs(tre - t) < FLOAT_TOLERANCE for d, t in pairs)
        if not pair_exists:
            return jsonify({'errors': ['Par DMSO+TREHALOSE não encontrado no dataset.']}), 400
        
        # Carregar modelo
        model = try_load_model(cell_type, variant='both')
        if model is None:
            return jsonify({'error': f"Modelo não encontrado para: {cell_type}"}), 404
        
        # Fazer predição
        input_dict = {col: 0.0 for col in MODEL_FEATURES}
        input_dict[FEATURE_MAP['DMSO']] = float(dmso)
        input_dict[FEATURE_MAP['TREHALOSE']] = float(tre)
        input_data = pd.DataFrame([input_dict])
        
        pred = 100 - model.predict(input_data)[0]
        viability = clamp_viability(pred)
        
        logger.info(f"Ambos: {cell_type} DMSO={dmso}%, TRE={tre}% -> {viability}")
        
        return jsonify({
            'viability': viability,
            'input': input_dict,
            'label': f"{int(dmso)}% + {int(tre)}%",
            'model_variant': 'both'
        })
    except Exception as e:
        logger.error(f"Erro em /predict-both: {e}", exc_info=True)
        return jsonify({'error': 'Erro interno ao prever par.'}), 500
@app.route('/model-metrics/<cell_type>')
def model_metrics(cell_type: str) -> object:
    """API: Retorna métricas do modelo (feature importances, etc)."""
    try:
        cell_type = cell_type.lower()
        
        is_valid, error = validate_cell_type(cell_type)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        variant = request.args.get('variant')
        model = try_load_model(cell_type, variant=variant)
        if model is None:
            return jsonify({'error': f"Modelo não encontrado: {cell_type}"}), 404
        
        # Extrair métricas do modelo
        feature_importances = getattr(model, 'feature_importances_', None)
        fi_list = feature_importances.tolist() if feature_importances is not None else None
        
        metrics = {
            'feature_importances': fi_list,
            'feature_names': MODEL_FEATURES,
            'n_features_in': getattr(model, 'n_features_in_', None),
            'variant': variant
        }
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Erro ao obter métricas para {cell_type}: {e}", exc_info=True)
        return jsonify({'error': 'Erro ao obter métricas.'}), 500
    

def _send_graph_file(cell_type: str, filename: str) -> object:
    """Serve arquivo de gráfico sem cache."""
    cell_type = cell_type.lower()
    response = send_from_directory(GRAPHS_DIR / cell_type, filename, cache_timeout=0)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response


@app.route('/graphs/<cell_type>/<path:filename>')
def serve_cell_graphs(cell_type: str, filename: str) -> object:
    """API: Serve gráficos HTML para cada tipo celular."""
    return _send_graph_file(cell_type, filename)


@app.route('/model-analysis/<cell_type>/<graph_name>')
def serve_model_analysis(cell_type: str, graph_name: str) -> object:
    """API: Serve análises dos modelos em HTML."""
    return _send_graph_file(cell_type, f"{graph_name}.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)