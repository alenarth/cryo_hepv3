bash
bash
---

# CryHepAI – Otimizador de Criopreservação de Hepatócitos

**Plataforma de predição e otimização de protocolos de criopreservação baseada em machine learning.**

---

## Visão Geral

CryHepAI é uma aplicação web desenvolvida para prever e otimizar a viabilidade celular pós-criopreservação de hepatócitos (e modelos animais) utilizando modelos de machine learning (XGBoost). O sistema integra dados experimentais históricos, análise estatística, explicabilidade via SHAP e uma interface interativa para simulação de misturas de crioprotetores.

---

## Funcionalidades Principais

- **Simulador de Viabilidade:** Predição em tempo real da viabilidade celular para diferentes tipos celulares e crioprotetores.
- **Mistura de Crioprotetores:** Permite simular e prever a viabilidade de misturas customizadas (2 a 5 compostos).
- **Explicabilidade:** Gráficos SHAP, curva de aprendizado, curva de validação, análise de resíduos e métricas detalhadas.
- **Interface Moderna:** UI responsiva com Bootstrap 5, gráficos Plotly e feedback visual.
- **API Documentada:** Swagger UI disponível em `/swagger` para consulta e testes de endpoints.

---

## Especificações Técnicas

### Estrutura do Projeto

```
cryo_hepv3/
│
├── app.py                  # Backend Flask principal, rotas e validações
├── config.py               # Configurações globais e features do modelo
├── train_models.py         # Script de treinamento e análise dos modelos
├── generate_model_reports.py # (opcional) Geração de relatórios extras
│
├── src/
│   ├── data/loader.py      # Carregamento e pré-processamento dos dados
│   ├── model/
│   │   ├── trainer.py      # Classe de treinamento (XGBoost)
│   │   ├── predictor.py    # Classe de predição e validação
│   ├── utils/constants.py  # Constantes auxiliares
│   └── visualization/plotter.py # Geração de gráficos e métricas
│
├── static/                 # Arquivos estáticos (CSS, JS, gráficos)
├── templates/              # Templates Jinja2 (HTML)
├── models/                 # Modelos treinados (.pkl)
├── data/
│   ├── raw/                # Dados brutos (CSV)
│   └── processed/          # Dados processados
└── tests/                  # Testes unitários
```

### Tecnologias e Bibliotecas

- **Backend:** Flask 3, Marshmallow, Flask-Limiter, Flask-Swagger-UI
- **Machine Learning:** XGBoost, scikit-learn, pandas, SHAP
- **Visualização:** Plotly, Matplotlib
- **Frontend:** Bootstrap 5, FontAwesome, Plotly.js
- **Documentação:** Swagger UI

### Modelagem e Algoritmo

- **Modelo:** XGBoost Regressor, um para cada tipo celular (`hepg2`, `rat`, `mice`)
- **Features:** `% DMSO`, `TREHALOSE`, `GLICEROL`, `SACAROSE`, `GLICOSE`
- **Target:** `% QUEDA DA VIABILIDADE`
- **Treinamento:** Validação rigorosa, split 80/20, métricas RMSE e R², análise de resíduos, explicabilidade SHAP
- **Predição:** O input é sempre um vetor com todas as features, preenchendo zero para crioprotetores não usados na mistura.

### Validações e Segurança

- **Validação de Inputs:** Marshmallow para schemas, limites de concentração, tipos celulares e crioprotetores válidos, proibição de duplicidade na mistura.
- **Rate Limiting:** 100 requisições/hora (global), 30/minuto para predição de mistura.
- **Logging:** Log detalhado de erros e operações críticas.
- **Swagger:** Documentação interativa dos endpoints.

---

## Instalação e Execução

### Pré-requisitos

- Python 3.9+
- pip

### Instalação

```bash
git clone https://github.com/seu-usuario/cryocell-predictor.git
cd cryocell-predictor
python -m venv venv
# Ative o ambiente virtual:
# Windows:
venv\\Scripts\\activate
# Linux/Mac:
source venv/bin/activate
pip install -r requirements.txt
```

### Preparação dos Dados

Coloque os arquivos de dados em `data/raw/`:
- `hepg2.csv`
- `rat.csv`
- `mice.csv`

### Treinamento dos Modelos

```bash
python train_models.py
```

Os modelos treinados serão salvos em `models/` e os gráficos em `static/graphs/`.

### Execução da Aplicação

```bash
python app.py
```

Acesse em: [http://localhost:5000](http://localhost:5000)

---

## Uso

- **Simulador de Viabilidade:** Escolha tipo celular, crioprotetor e concentração para visualizar curva e ponto ótimo.
- **Mistura de Crioprotetores:** Adicione 2 a 5 crioprotetores, defina concentrações e obtenha a viabilidade prevista.
- **Área do Desenvolvedor:** Visualize métricas, gráficos de explicabilidade e análise de erros dos modelos.

---

## Testes

Execute os testes unitários com:

```bash
pytest tests/
```

---

## Especificações Avançadas

- **Arquitetura Modular:** Separação clara entre backend, lógica de ML, visualização e frontend.
- **Explicabilidade:** SHAP para análise de impacto de cada feature na predição.
- **Curvas de Aprendizado e Validação:** Geração automática para cada modelo.
- **Interface Responsiva:** Totalmente adaptada para desktop e mobile.
- **Extensibilidade:** Fácil inclusão de novos tipos celulares ou crioprotetores via configuração.

---

## Licença

MIT. Veja o arquivo `LICENSE.md`.

---

Se quiser incluir exemplos de uso da API, prints ou fluxogramas, posso complementar!