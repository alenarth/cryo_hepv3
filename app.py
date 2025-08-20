from flask import Flask, render_template, request, jsonify, send_from_directory
import joblib
import pandas as pd
from pathlib import Path
from config import Config
from functools import lru_cache
import logging
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint
from marshmallow import Schema, fields, ValidationError, validates_schema

CONCENTRATION_RANGES = {
    'DMSO': list(range(0, 101, 5)),
    'TREHALOSE': [0, 0.97, 1.94, 3.88, 7.77, 15.54, 31.08, 62.16, 100],
    'GLICEROL': list(range(0, 101, 5)),
    'SACAROSE': list(range(0, 101, 5)),
    'GLICOSE': list(range(0, 101, 5)),
}


# Configuração via ambiente
MODELS_DIR = Path(os.getenv('MODELS_DIR', Config.MODELS_DIR))
GRAPHS_DIR = Path(os.getenv('GRAPHS_DIR', Config.GRAPHS_DIR))

app = Flask(__name__)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Rate limiting
limiter = Limiter(get_remote_address, app=app, default_limits=["100 per hour"])

# Swagger
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL, config={'app_name': "Cryo Hepatocytes API"})
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Marshmallow schemas
class PredictSchema(Schema):
    cell_type = fields.Str(required=True)
    cryoprotector = fields.Str(required=True)

class SpecificPredictSchema(PredictSchema):
    concentration = fields.Float(required=True)


# --- Schemas para mistura ---
class MixtureCryoprotectantSchema(Schema):
    cryoprotector = fields.Str(required=True)
    concentration = fields.Float(required=True)


class MixturePredictSchema(Schema):
    cell_type = fields.Str(required=True)
    mixture = fields.List(fields.Nested(MixtureCryoprotectantSchema), required=True, validate=lambda lst: 2 <= len(lst) <= 5)

    @validates_schema
    def validate_cryoprotectors(self, data, **kwargs):
        cps = [item['cryoprotector'].upper() for item in data.get('mixture', [])]
        if len(set(cps)) != len(cps):
            raise ValidationError('Não repita crioprotetores na mistura.')
        for cp in cps:
            if cp not in VALID_CRYOPROTECTORS:
                raise ValidationError(f'Crioprotetor inválido: {cp}')

# --- Auxiliares ---
@app.route('/mixture')
def mixture_page():
    """Página de mistura de crioprotetores."""
    return render_template('mixture.html', config=Config)


@app.route('/predict-mixture', methods=['POST'])
@limiter.limit("30/minute")
def predict_mixture():
    """Prediz viabilidade para uma mistura de crioprotetores."""
    try:
        data = request.json

        # Validação de schema e quantidade de crioprotetores
        try:
            MixturePredictSchema().load(data)
        except ValidationError as ve:
            return jsonify({'errors': ve.messages}), 400
        cell_type = data['cell_type'].lower()
        mixture = data['mixture']
        errors = []
        if cell_type not in VALID_CELL_TYPES:
            errors.append(f"Tipo celular inválido: {cell_type}")
        if len(mixture) < 2:
            errors.append("Adicione pelo menos 2 crioprotetores.")
        if errors:
            return jsonify({'errors': errors}), 400

        # Mapeamento robusto dos crioprotetores para as features do modelo
        feature_map = {
            'DMSO': '% DMSO',
            'TREHALOSE': 'TREHALOSE',
            'GLICEROL': 'GLICEROL',
            'SACAROSE': 'SACAROSE',
            'GLICOSE': 'GLICOSE'
        }
        input_dict = {feat: 0 for feat in feature_map.values()}
        for item in mixture:
            cp_raw = item['cryoprotector']
            cp = str(cp_raw).strip().upper()
            if cp not in feature_map:
                return jsonify({'errors': [f"Crioprotetor inválido: {cp_raw}"]}), 400
            conc = float(item['concentration'])
            input_dict[feature_map[cp]] = conc

        input_data = pd.DataFrame([input_dict])
        model = get_model(cell_type)
        predicted_drop = model.predict(input_data)[0]
        viability = float(round(max(0, min(100, 100 - predicted_drop)), 1))
        return jsonify({
            'viability': viability,
            'input': input_dict
        })
    except ValidationError as ve:
        return jsonify({'errors': ve.messages}), 400
    except Exception as e:
        logging.error(f"Erro interno na mistura: {str(e)}")
        return jsonify({'error': 'Erro interno ao prever mistura.', 'details': str(e)}), 500

VALID_CELL_TYPES = {'hepg2', 'mice', 'rat'}
VALID_CRYOPROTECTORS = {'DMSO', 'TREHALOSE', 'GLICEROL', 'SACAROSE', 'GLICOSE'}

def validate_input(cell_type: str, cryoprotector: str) -> list[str]:
    errors = []
    if cell_type.lower() not in VALID_CELL_TYPES:
        errors.append(f"Tipo celular inválido: {cell_type}")
    if cryoprotector.upper() not in VALID_CRYOPROTECTORS:
        errors.append(f"Crioprotetor inválido: {cryoprotector}")
    return errors

# Cache simples para modelos
@lru_cache(maxsize=8)
def get_model(cell_type: str):
    return joblib.load(MODELS_DIR / f"xgboost_{cell_type}.pkl")

@app.route('/')
def index() -> str:
    """Página inicial do sistema."""
    return render_template('index.html', config=Config)


@app.route('/developer')
def developer_area() -> str:
    """Área do desenvolvedor."""
    # Valor padrão: primeiro tipo celular
    selected_cell_type = Config.CELL_TYPES[0] if Config.CELL_TYPES else ''
    return render_template('developer.html', config=Config, selected_cell_type=selected_cell_type)




@app.route('/predict', methods=['POST'])
@limiter.limit("30/minute")

def predict() -> object:
    """Retorna viabilidade para todas as concentrações e a concentração ótima."""
    try:
        data = request.json
        # Validação Marshmallow
        PredictSchema().load(data)
        cell_type = data.get('cell_type', '').lower()
        cryoprotector = data.get('cryoprotector', '').upper()
        errors = validate_input(cell_type, cryoprotector)
        if errors:
            logging.warning(f"Erro de entrada: {errors}")
            return jsonify({'errors': errors}), 400
        model = get_model(cell_type)
        concentrations = CONCENTRATION_RANGES.get(cryoprotector, list(range(0, 101, 5)))
        viability = []
        for conc in concentrations:
            input_data = pd.DataFrame([{
                '% DMSO': conc if cryoprotector == 'DMSO' else 0,
                'TREHALOSE': conc if cryoprotector == 'TREHALOSE' else 0,
                'GLICEROL': conc if cryoprotector == 'GLICEROL' else 0,
                'SACAROSE': conc if cryoprotector == 'SACAROSE' else 0,
                'GLICOSE': conc if cryoprotector == 'GLICOSE' else 0
            }])
            pred = 100 - model.predict(input_data)[0]
            viability.append(float(round(max(0, min(100, pred)), 1)))
        max_viab = max(viability)
        opt_index = viability.index(max_viab)
        logging.info(f"Previsão: {cell_type}, {cryoprotector}, ótimo: {concentrations[opt_index]} -> {max_viab}")
        return jsonify({
            'concentrations': concentrations,
            'viability': viability,
            'optimal': {
                'concentration': concentrations[opt_index],
                'value': float(max_viab)
            }
        })
    except ValidationError as ve:
        logging.warning(f"Erro de validação: {ve.messages}")
        return jsonify({'errors': ve.messages}), 400
    except Exception as e:
        logging.error(f"Erro interno: {str(e)}")
        return jsonify({'error': 'Erro interno ao prever viabilidade.', 'details': str(e)}), 500



@app.route('/specific-predict', methods=['POST'])
@limiter.limit("30/minute")

def specific_predict() -> object:
    """Retorna viabilidade para uma concentração específica."""
    try:
        data = request.json
        SpecificPredictSchema().load(data)
        cell_type = data.get('cell_type', '').lower()
        cryoprotector = data.get('cryoprotector', '').upper()
        concentration = data.get('concentration')
        errors = validate_input(cell_type, cryoprotector)
        allowed_concs = CONCENTRATION_RANGES.get(cryoprotector, list(range(0, 101, 5)))
        if concentration is None:
            errors.append('Concentração não informada.')
        else:
            try:
                concentration = float(concentration)
                # Aceita se estiver próximo de algum valor permitido (tolerância para floats)
                if not any(abs(concentration - float(c)) < 1e-2 for c in allowed_concs):
                    errors.append(f'Concentração inválida para {cryoprotector}. Valores permitidos: {allowed_concs}')
            except Exception:
                errors.append('Concentração deve ser um número.')
        if errors:
            logging.warning(f"Erro de entrada: {errors}")
            return jsonify({'errors': errors}), 400
        model = get_model(cell_type)
        input_data = pd.DataFrame([{
            '% DMSO': concentration if cryoprotector == 'DMSO' else 0,
            'TREHALOSE': concentration if cryoprotector == 'TREHALOSE' else 0,
            'GLICEROL': concentration if cryoprotector == 'GLICEROL' else 0,
            'SACAROSE': concentration if cryoprotector == 'SACAROSE' else 0,
            'GLICOSE': concentration if cryoprotector == 'GLICOSE' else 0
        }])
        predicted_drop = model.predict(input_data)[0]
        viability = float(round(max(0, min(100, 100 - predicted_drop)), 1))
        logging.info(f"Previsão específica: {cell_type}, {cryoprotector}, {concentration} -> {viability}")
        return jsonify({
            'viability': viability,
            'cell_type': cell_type.upper(),
            'cryoprotector': cryoprotector,
            'concentration': concentration
        })
    except ValidationError as ve:
        logging.warning(f"Erro de validação: {ve.messages}")
        return jsonify({'errors': ve.messages}), 400
    except Exception as e:
        logging.error(f"Erro interno: {str(e)}")
        return jsonify({'error': 'Erro interno ao prever viabilidade.', 'details': str(e)}), 500
@app.route('/model-metrics/<cell_type>')
def model_metrics(cell_type: str) -> object:
    """Retorna métricas do modelo para o tipo celular."""
    try:
        if cell_type not in VALID_CELL_TYPES:
            return jsonify({'error': 'Tipo celular inválido.'}), 400
        model = get_model(cell_type)
        # Exemplo: retorna apenas feature_importances_ e n_features_in_
        metrics = {
            'feature_importances': model.feature_importances_.tolist() if hasattr(model, 'feature_importances_') else None,
            'n_features_in': getattr(model, 'n_features_in_', None)
        }
        return jsonify(metrics)
    except Exception as e:
        logging.error(f"Erro ao obter métricas: {str(e)}")
        return jsonify({'error': 'Erro ao obter métricas.', 'details': str(e)}), 500
    

@app.route('/graphs/<cell_type>/<path:filename>')
def serve_cell_graphs(cell_type: str, filename: str) -> object:
    """Serve arquivos de gráficos para cada tipo celular."""
    return send_from_directory(Config.GRAPHS_DIR / cell_type, filename)


@app.route('/model-analysis/<cell_type>/<graph_name>')
def serve_model_analysis(cell_type: str, graph_name: str) -> object:
    """Serve análises dos modelos em HTML."""
    return send_from_directory(
        Config.GRAPHS_DIR / cell_type,
        f"{graph_name}.html"
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)