from flask import Flask, render_template, request, jsonify, send_from_directory
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from config import Config

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', config=Config)

@app.route('/developer')
def developer_area():
    return render_template('developer.html', config=Config)


@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        cell_type = data['cell_type']
        cryoprotector = data['cryoprotector']
        
        model = joblib.load(Config.MODELS_DIR / f"xgboost_{cell_type}.pkl")
        concentrations = list(range(0, 101, 5))
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
        
        return jsonify({
            'concentrations': concentrations,
            'viability': viability,
            'optimal': {
                'concentration': int(concentrations[opt_index]),
                'value': float(max_viab)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/specific-predict', methods=['POST'])
def specific_predict():
    try:
        data = request.json
        cell_type = data['cell_type']
        cryoprotector = data['cryoprotector']
        concentration = int(data['concentration'])

        if concentration % 5 != 0 or not (0 <= concentration <= 100):
            return jsonify({'error': 'Concentração inválida. Use múltiplos de 5% entre 0-100'}), 400

        model = joblib.load(Config.MODELS_DIR / f"xgboost_{cell_type}.pkl")
        
        input_data = pd.DataFrame([{
            '% DMSO': concentration if cryoprotector == 'DMSO' else 0,
            'TREHALOSE': concentration if cryoprotector == 'TREHALOSE' else 0,
            'GLICEROL': concentration if cryoprotector == 'GLICEROL' else 0,
            'SACAROSE': concentration if cryoprotector == 'SACAROSE' else 0,
            'GLICOSE': concentration if cryoprotector == 'GLICOSE' else 0
        }])

        predicted_drop = model.predict(input_data)[0]
        viability = float(round(max(0, min(100, 100 - predicted_drop)), 1))

        return jsonify({
            'viability': viability,
            'cell_type': cell_type.upper(),
            'cryoprotector': cryoprotector,
            'concentration': concentration
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/graphs/<cell_type>/<path:filename>')
def serve_cell_graphs(cell_type, filename):
    return send_from_directory(Config.GRAPHS_DIR / cell_type, filename)

@app.route('/model-analysis/<cell_type>/<graph_name>')
def serve_model_analysis(cell_type, graph_name):
    return send_from_directory(
        Config.GRAPHS_DIR / cell_type,
        f"{graph_name}.html"
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)