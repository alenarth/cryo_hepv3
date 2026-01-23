# CryHepAI: Predição de Viabilidade Celular Pós-Criopreservação

Sistema de aprendizado de máquina para predição de viabilidade celular baseado em concentrações de crioprotetores (DMSO e TREHALOSE). Utiliza regressão XGBoost treinada em dados experimentais de criopreservação de hepatócitos.

## Características Principais

- **3 tipos celulares**: HepG2 (linhagem hepatocelular), camundongo, rato
- **4 variantes de modelo** por tipo celular:
  - `default`: Dados puros (apenas DMSO OU apenas TREHALOSE)
  - `dmso_only`: Apenas amostras com TREHALOSE = 0%
  - `trehalose_only`: Apenas amostras com DMSO = 0%
  - `both`: Combinações de DMSO + TREHALOSE simultâneos
- **11 endpoints REST** para diferentes casos de uso
- **Interface web** interativa com gráficos em tempo real
- **Análise de impacto de variáveis** via SHAP (SHapley Additive exPlanations)
- **Visualizações avançadas**: curvas de aprendizado, plots de validação, distribuição de erros

## Requisitos

- Python 3.10+
- Dependências: Flask, XGBoost, Pandas, NumPy, Plotly, SHAP, Joblib

Para lista completa, veja `requirements.txt`.

## Instalação e Execução

### Setup Inicial

```bash
# Clonar repositório
git clone <repo>
cd cryo_hepv3

# Criar ambiente virtual
python -m venv venv
source venv/Scripts/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### Executar Aplicação

```bash
python app.py
```

A aplicação estará disponível em `http://localhost:5000`.

### Treinar Modelos

Para retreinar ou atualizar os modelos com novos dados:

```bash
python train_models.py
```

Este script:
- Carrega dados dos CSVs em `data/raw/`
- Remove amostras contaminadas (0% DMSO AND 0% TREHALOSE)
- Treina 12 modelos XGBoost (3 tipos celulares × 4 variantes)
- Gera gráficos de desempenho em `static/graphs/`
- Salva modelos em `models/`

## API - Endpoints

### 1. Predição de Range (Curva Dose-Resposta)

```http
POST /predict
Content-Type: application/json

{
  "cell_type": "hepg2",
  "cryoprotector": "DMSO"
}
```

**Resposta:**
```json
{
  "concentrations": [0, 5, 10, 15, ...],
  "viability": [100.0, 95.2, 88.5, 81.3, ...],
  "optimal": {
    "concentration": 5,
    "value": 97.8
  },
  "model_variant": "default"
}
```

### 2. Predição para Concentração Específica

```http
POST /specific-predict
Content-Type: application/json

{
  "cell_type": "hepg2",
  "cryoprotector": "DMSO",
  "concentration": 7.5
}
```

**Resposta:**
```json
{
  "viability": 92.3,
  "viability_loss": 7.7,
  "confidence": 0.94
}
```

### 3. Predição de Mistura (2-5 Crioprotetores)

```http
POST /predict-mixture
Content-Type: application/json

{
  "cell_type": "hepg2",
  "mixture": [
    {"cryoprotector": "DMSO", "concentration": 5.0},
    {"cryoprotector": "TREHALOSE", "concentration": 2.0}
  ]
}
```

**Resposta:**
```json
{
  "viability": 96.5,
  "components": [
    {"cryoprotector": "DMSO", "contribution": 45.2},
    {"cryoprotector": "TREHALOSE", "contribution": 51.3}
  ]
}
```

### 4. Predição de Pares (DMSO + TREHALOSE)

```http
POST /predict-both
Content-Type: application/json

{
  "cell_type": "hepg2",
  "dmso": 5.0,
  "trehalose": 2.0
}
```

**Resposta:**
```json
{
  "concentrations": ["5% + 0%", "5% + 2%", "5% + 4%", ...],
  "viability": [95.0, 97.8, 99.1, ...],
  "optimal": {
    "concentration": "5% + 5%",
    "value": 100.0
  },
  "model_variant": "both"
}
```

### 5. Combinações Disponíveis

```http
GET /available-both/hepg2
```

Retorna todas as combinações DMSO+TREHALOSE presentes nos dados de treino.

### 6. Avaliação de Desempenho

```http
POST /evaluate
Content-Type: application/json

{
  "cell_type": "hepg2",
  "model_variant": "default"
}
```

Retorna métricas: MAE, RMSE, R², validação cruzada.

### 7. Verificação de Saúde

```http
GET /health
```

### 8. Listagem de Modelos

```http
GET /models
```

Retorna lista de modelos treinados disponíveis.

### 9-11. Páginas Web

- `GET /`: Interface principal (simulador)
- `GET /developer`: Área de desenvolvedor (análises avançadas)
- `GET /mixture`: Página dedicada a misturas

## Estrutura de Diretórios

```
cryo_hepv3/
├── app.py                    # Flask REST API (11 endpoints)
├── train_models.py          # Script de treinamento
├── requirements.txt         # Dependências Python
├── CONTEXT.md              # Documentação técnica (histórico e decisões)
├── README.md               # Este arquivo
│
├── src/
│   ├── constants.py        # Configurações centralizadas
│   ├── data/
│   │   └── loader.py       # Carregamento de CSV
│   ├── model/
│   │   └── trainer.py      # CryoModelTrainer (treinamento e predição)
│   ├── utils/
│   │   └── helpers.py      # Funções auxiliares (validação, clamping)
│   └── visualization/
│       └── plotter.py      # Geração de gráficos e SHAP analysis
│
├── data/raw/
│   ├── hepg2.csv          # 56 amostras (limpas)
│   ├── rat.csv            # Dados de rato
│   ├── mice.csv           # Dados de camundongo
│   ├── mapping.csv        # Mapeamento de colunas
│   └── backups/           # Backups com timestamps
│
├── models/                 # Modelos XGBoost treinados (.pkl)
│   ├── hepg2_default.pkl
│   ├── hepg2_dmso_only.pkl
│   ├── hepg2_trehalose_only.pkl
│   ├── hepg2_both.pkl
│   └── ... (12 modelos total)
│
├── static/
│   ├── css/
│   │   └── styles.css      # Estilos (Bootstrap 5 + customizações)
│   ├── js/
│   │   ├── app.js          # Lógica de interface principal
│   │   └── developer.js    # Utilitários para desenvolvedor
│   └── graphs/             # Gráficos gerados por tipo celular
│       ├── hepg2/
│       ├── rat/
│       └── mice/
│
├── templates/
│   ├── index.html          # Interface principal
│   ├── developer.html      # Análises avançadas
│   ├── _footer.html        # Rodapé (incluído)
│   └── _help_modal.html    # Modal de ajuda (incluído)
```

## Formato de Dados de Treino

Arquivos CSV em `data/raw/` devem conter as colunas:

```csv
DMSO (%),TREHALOSE (%),% Viability Loss
0,5,2.1
5,0,1.8
10,0,3.2
5,5,0.9
```

### Processamento de Dados

Durante o treinamento:
1. Leitura dos CSVs
2. **Remoção de controles contaminados**: Amostras com DMSO=0 AND TREHALOSE=0 são excluídas (dados inválidos)
3. Para variante `default`: Aplicação de XOR (apenas DMSO OU TREHALOSE, não ambos)
4. Divisão treino/validação (80/20)
5. Normalização de features

## Configuração

Editar `src/constants.py` para modificar:

```python
CELL_TYPES = ['hepg2', 'rat', 'mice']
MODEL_VARIANTS = ['default', 'dmso_only', 'trehalose_only', 'both']
CRYOPROTECTANTS = ['DMSO', 'TREHALOSE']
CONCENTRATION_RANGES = {
    'DMSO': list(range(0, 101, 5)),      # 0-100%, step 5%
    'TREHALOSE': list(range(0, 101, 5))
}
```

## Variantes de Modelo - Explicação Detalhada

### DEFAULT
- **Uso**: Predição com crioprotetor único
- **Dados**: Apenas amostras puras (DMSO>0 AND TREHALOSE=0) OR (DMSO=0 AND TREHALOSE>0)
- **Aplicação**: Protocolos com apenas um agente crioprotetor

### DMSO_ONLY
- **Uso**: Predição focada em DMSO
- **Dados**: Todas as amostras onde TREHALOSE = 0%
- **Aplicação**: Estudos específicos com DMSO

### TREHALOSE_ONLY
- **Uso**: Predição focada em TREHALOSE
- **Dados**: Todas as amostras onde DMSO = 0%
- **Aplicação**: Estudos específicos com TREHALOSE

### BOTH
- **Uso**: Predição de combinações sinérgicas
- **Dados**: Todas as amostras (incluindo misturas)
- **Aplicação**: Otimização de protocolos com múltiplos agentes

## Performance Esperada

Métricas dos modelos (validação cruzada k-fold):
- **MAE** (Mean Absolute Error): < 5% viabilidade
- **RMSE** (Root Mean Square Error): < 7%
- **R²** (Coeficiente de Determinação): > 0.85

Visualizações geradas:
- Curva dose-resposta
- Real vs. Predito (scatter plot)
- Distribuição de erros
- SHAP importance e summary plots
- Curva de aprendizado
- Curva de validação

## Interface Web

### Página Principal (`/`)
- Seleção de tipo celular
- Escolha de crioprotetor (DMSO, TREHALOSE, ou BOTH)
- Slider de concentração
- Gráfico interativo com curva dose-resposta
- Ponto ótimo destacado

### Área de Desenvolvedor (`/developer`)
- Seleção de modelo treinado
- Métricas de desempenho agregadas
- Gráficos interativos: real vs. predito, SHAP, distribuição de erros
- Análises de impacto de variáveis
- Curves: aprendizado e validação

## Desenvolvimento

### Adicionar Novo Tipo Celular

1. Adicionar CSV em `data/raw/` com nome `{cell_type}.csv`
2. Atualizar `src/constants.py`: adicionar à lista `CELL_TYPES`
3. Executar `python train_models.py`

### Adicionar Nova Feature

1. Atualizar formato de dados em `src/data/loader.py`
2. Modificar `MODEL_FEATURES` em `src/constants.py`
3. Retreinar: `python train_models.py`

### Modificar Hiperparâmetros XGBoost

Editar `src/model/trainer.py`, método `train()`:

```python
self.model = xgb.XGBRegressor(
    max_depth=5,          # Profundidade máxima
    learning_rate=0.1,    # Taxa de aprendizado
    n_estimators=200,     # Número de árvores
    subsample=0.8         # Fração de amostras por árvore
)
```

## Troubleshooting

### Erro: "Modelos não encontrados"
- Executar `python train_models.py` para treinar

### Erro: "Arquivo CSV não encontrado"
- Verificar se CSVs estão em `data/raw/`
- Confirmar nomes de arquivo e colunas

### Gráficos não carregam
- Verificar se `train_models.py` foi executado
- Validar permissões em `static/graphs/`

### Predições inconsistentes
- Verificar se dados foram limpos corretamente
- Confirmar formato do JSON na requisição
- Validar concentrações dentro de ranges esperados

## Referências

- CONTEXT.md: Decisões arquiteturais e histórico do projeto
- XGBoost: https://xgboost.readthedocs.io/
- SHAP: https://shap.readthedocs.io/
- Flask: https://flask.palletsprojects.com/
