# Otimizador de Criopreservação de Hepatócitos 
**Hepatocytes Cryopreservation Solutions**  

---

## Overview  
Otimizador de Criopreservação de Hepatócitos é uma plataforma integrada que combina técnicas avançadas de machine learning com conhecimentos de criobiologia para prever e otimizar protocolos de preservação celular. Desenvolvido para pesquisadores médicos e técnicos de laboratório, o sistema utiliza modelos XGBoost treinados em dados experimentais históricos para determinar combinações ideais de crioprotetores, maximizando a viabilidade celular pós-congelamento.

---

## Key Features  
- **Predição em Tempo Real**: Interface web interativa com atualização instantânea de resultados  
- **Análise Dose-Resposta**: Visualização dinâmica de curvas de viabilidade para até 5 crioprotetores  
- **Explicabilidade Científica**: Gráficos SHAP e importância de variáveis para interpretação de resultados  
- **Validação Estatística**: Métricas de desempenho detalhadas (RMSE, R²) e intervalos de confiança  
- **Arquitetura Modular**: Separação clara entre camadas de dados, modelagem e visualização  

---

## Instalação  
1. **Pré-requisitos**:  
   - Python 3.9+  
   - pip 23.0+  

2. **Setup**:  
```bash
git clone https://github.com/seu-usuario/cryocell-predictor.git
cd cryocell-predictor
python -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```
3. **Preparação de Dados**:

Coloque os arquivos CSV em data/raw/

Formato requerido: hepg2.csv, rat.csv, mice.csv

Train Models:

bash
Copy
python train_models.py
Run Application:

bash
Copy
python app.py
Acesse: http://localhost:5000