# Cryo-HepV3: Hepatocyte Viability Prediction

ML system predicting cryopreserved hepatocyte viability based on cryoprotectant concentrations.

## Quick Start

```bash
# Setup
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)
pip install -r requirements.txt

# Run
python app.py
# Visit: http://localhost:5000
```

## Train Models

```bash
python train_models.py
```

Trains 12 XGBoost models (3 cell types × 4 variants).

## API Endpoints

### Predict Range
```bash
POST /predict
{"cell_type": "hepg2", "cryoprotector": "DMSO"}
```

### Predict Specific
```bash
POST /specific-predict
{"cell_type": "hepg2", "cryoprotector": "DMSO", "concentration": 10.5}
```

### Predict Mixture
```bash
POST /predict-mixture
{
  "cell_type": "hepg2",
  "mixture": [
    {"cryoprotector": "DMSO", "concentration": 5},
    {"cryoprotector": "TREHALOSE", "concentration": 2}
  ]
}
```

### Predict Pair
```bash
POST /predict-both
{"cell_type": "hepg2", "dmso": 5.0, "trehalose": 2.0}
```

### Available Combinations
```bash
GET /available-both/hepg2
```

## Structure

```
src/
  ├── constants.py        # Config
  ├── utils/helpers.py    # Validation
  ├── model/              # Training & prediction
  └── visualization/      # Plots

data/raw/                 # CSV datasets
models/                   # Trained models
static/                   # CSS, JS, graphs
templates/                # HTML interface
```

## Configuration

Edit `src/constants.py`:
- Cell types: `hepg2`, `rat`, `mice`
- Cryoprotectors: `DMSO`, `TREHALOSE`, `BOTH`
- Concentration ranges & validation

## Data Format

```
% DMSO,TREHALOSE,% QUEDA DA VIABILIDADE
0,0,2.5
5,0,1.8
10,0,3.2
```

## Requirements

Python 3.10+, Flask, XGBoost, Pandas, Joblib, Plotly

See `requirements.txt` for versions.
