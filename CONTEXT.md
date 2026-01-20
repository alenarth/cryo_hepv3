# CONTEXTO DO PROJETO - cryo_hepv3

**Data**: 20 de Janeiro de 2026  
**Status**: Backend concluído e validado. Frontend pronto para melhorias.

---

## 🎯 FILOSOFIA DO PROJETO

### "O melhor código é o que você pode cortar"

Este projeto segue rigorosamente o princípio de **simplicidade e minimalismo**:
- ❌ **NÃO fazer**: Overengineering, features "para o futuro", código duplicado
- ✅ **FAZER**: Apenas o essencial, código limpo e enxuto, máxima clareza
- Remover: Rate limiting, validação desnecessária, endpoints não-usados
- Resultado: Código mantível, rápido, sem dívida técnica

---

## 📊 ESTRUTURA DO PROJETO

```
cryo_hepv3/
├── app.py          # Flask REST API com 11 endpoints
├── train_models.py                # Script para treinar modelos
├── requirements.txt               # Dependências
├── README.md                      # Documentação
│
├── src/
│   ├── constants.py              # Constantes centralizadas (62 linhas)
│   ├── data/
│   │   └── loader.py             # Carregamento de CSVs
│   ├── model/
│   │   ├── trainer.py            # CryoModelTrainer (81 linhas)
│   │   ├── model.py              # DELETADO - inline na trainer
│   │   └── predictor.py          # DELETADO - inline na trainer
│   ├── utils/
│   │   └── helpers.py            # Funções auxiliares (299 linhas)
│   └── visualization/
│       └── plotter.py            # Geração de gráficos
│
├── data/raw/
│   ├── hepg2.csv                 # 56 amostras (LIMPAS)
│   ├── rat.csv                   # Dados de rato
│   ├── mice.csv                  # Dados de camundongo
│   └── mapping.csv               # Mapeamento de colunas
│
├── models/                        # XGBoost .pkl files (12 por tipo de célula)
├── templates/
│   ├── index.html                # Interface principal
│   ├── developer.html            # Área de desenvolvedor
│   └── _*.html                   # Componentes
│
├── static/
│   ├── css/styles.css            # Estilos
│   ├── js/app.js                 # JavaScript frontend
│   ├── js/developer.js           # JavaScript desenvolvedor
│   └── graphs/                   # Gráficos HTML/PNG
│

```

---

## 🔧 STACK TÉCNICO

**Backend**:
- Flask 2.x (REST API)
- XGBoost (Modelos ML)
- Pandas (Processamento de dados)
- Plotly/SHAP (Visualizações)
- Python 3.10+

**Frontend**:
- HTML5
- CSS3 (Bootstrap)
- JavaScript vanilla
- Plotly.js (gráficos interativos)

**Dependências REMOVIDAS**:
- ❌ flask-limiter (rate limiting)
- ❌ marshmallow (validação)
- ❌ flask-swagger-ui
- ❌ config.py (inlined)

---

## 🧠 LÓGICA DO BACKEND

### Dados de Treino
- **Fonte**: CSV com colunas: `DMSO (%)`, `TREHALOSE (%)`, `% Viability Loss`
- **Limpeza**: Exclui amostras onde DMSO=0 E TREHALOSE=0 (controles contaminados)
- **Variantes de modelo**:
  - `DEFAULT`: Treina com dados puros (XOR: só DMSO OU só TREHALOSE)
  - `DMSO_only`: Só amostras com TREHALOSE=0
  - `TREHALOSE_only`: Só amostras com DMSO=0
  - `BOTH`: Todas as amostras (para combinar cryoprotectores)

### Endpoints (11 total)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/predict` | Prediz viabilidade para um cryoprotector (DMSO ou TREHALOSE) |
| POST | `/predict-mixture` | Prediz viabilidade para 2-5 cryoprotectores |
| POST | `/predict-both` | Retorna combinações DMSO+TREHALOSE do dataset |
| POST | `/specific-predict` | Prediz para concentração específica |
| GET | `/` | Interface principal |
| GET | `/developer` | Área de desenvolvedor com gráficos |
| GET | `/mixture` | Página de misturas |
| GET | `/health` | Health check |
| GET | `/models` | Lista modelos disponíveis |
| POST | `/evaluate` | Avalia performance do modelo |
| ~~POST~~ | ~~`/train-variants`~~ | **REMOVIDO - desenvolvimento apenas** |

### Formatos de Requisição/Resposta

**POST /predict**:
```json
{
  "cryoprotectant": "DMSO",     // ou "TREHALOSE"
  "concentration": 10,           // 0-100
  "cell_type": "hepg2"          // hepg2, rat, mice
}
```

**Resposta**:
```json
{
  "viability_loss": 5.2,
  "viability_percentage": 94.8,
  "confidence": 0.95,
  "model_variant": "default"
}
```

**POST /predict-both**:
```json
{
  "cell_type": "hepg2"
}
```

**Resposta**:
```json
{
  "concentrations": ["5% + 5%", "5% + 10%", ...],
  "viability": [95.0, 100.0, ...],
  "optimal": {
    "concentration": "5% + 20%",
    "value": 100.0
  },
  "model_variant": "both"
}
```

---

## 🐛 BUGS DESCOBERTOS E CORRIGIDOS (SESSÃO ANTERIOR)

### 1. **Data Contaminada** ⚠️ CRÍTICO
- **Problema**: Modelos treinados com controles misturados
- **Sintoma**: Amostras com 0% DMSO tinham viabilidade 62.8% (biologicamente incorreto)
- **Causa**: 46 amostras com DMSO=0 E TREHALOSE=0 com valores variáveis
- **Solução**: Filtro em `trainer.py` que exclui essas amostras + XOR para DEFAULT

### 2. **JSON Serialization Error**
- **Arquivo**: `app.py` linha ~120
- **Problema**: `render_template()` recebia objeto Config em vez de dict
- **Solução**: Passar `config.to_dict()` ou inline dict com valores

### 3. **Undefined References**
- **Arquivo**: `helpers.py` linha 239
- **Problema**: `Config.RAW_DATA_DIR` não existia
- **Solução**: Definir `RAW_DATA_DIR` inline em cada arquivo

### 4. **Endpoint /train-variants**
- **Problema**: Endpoint desnecessário para produção
- **Solução**: REMOVIDO (linha 157 app.py, developer.html line 56)

---

## ✅ VALIDAÇÕES FEITAS

1. **Dados limpos**: ✅ Amostras contaminadas removidas
2. **Monotocidade das predições**: ✅ Dose-resposta correto
3. **Biologia**: ✅ Viabilidade aumenta com concentração (esperado)
4. **API endpoints**: ✅ Todos retornam HTTP 200
5. **Sem erros Python**: ✅ Syntax check passou

---

## 🎨 FRONTEND - ESTADO ATUAL

### Arquivos
- `templates/index.html` - Interface principal (formulário + resultados)
- `templates/developer.html` - Gráficos de modelos (CLEANADO)
- `templates/mixture.html` - Página de misturas
- `static/js/app.js` - Lógica de interface
- `static/css/styles.css` - Estilos

### O Que Precisa Fazer

**Prioridade ALTA**:
1. Melhorar CSS (Bootstrap atualizado, responsivo)
2. Adicionar validação de entrada (min/max)
3. Melhorar UX: feedback visual, loading states
4. Mobile responsiveness

**Prioridade MÉDIA**:
1. Gráficos interativos (Plotly.js)
2. Tabelas com resultados históricos
3. Temas claro/escuro

**Prioridade BAIXA**:
1. Animações
2. Internacionalização

---

## 📝 ARQUIVOS CRÍTICOS E SUAS FUNÇÕES

### app.py (490 linhas)
- Define todos os 11 endpoints
- Imports: `flask`, `pandas`, `xgboost`, `plotly`, `shap`
- Constantes inline: `CONCENTRATION_RANGES`, `MODEL_FEATURES`, `FEATURE_MAP`
- **NÃO MODIFICAR**: Lógica de predição testada e validada

### src/constants.py
```python
CELL_TYPES = ['hepg2', 'rat', 'mice']
MODEL_VARIANTS = ['default', 'dmso_only', 'trehalose_only', 'both']
CRYOPROTECTANTS = ['DMSO', 'TREHALOSE']
MODEL_PATH = Path(__file__).parent.parent / "models"
```

### src/utils/helpers.py
- **get_available_both_combinations()**: Encontra pares DMSO+TREHALOSE no dataset
- **clamp_viability()**: Garante viabilidade entre 0-100%
- **RAW_DATA_DIR**: Caminho para CSVs

### src/model/trainer.py
```python
# FILTRO CRÍTICO - Não remover!
if variant == 'default':
    # Exclui 0% DMSO AND 0% TREHALOSE (controles contaminados)
    df = df[~((df['DMSO'] == 0) & (df['TREHALOSE'] == 0))]
    # Usa apenas dados puros (XOR)
    df = df[((df['DMSO'] > 0) & (df['TREHALOSE'] == 0)) | 
            ((df['DMSO'] == 0) & (df['TREHALOSE'] > 0))]
```

---


## 📌 RESUMO DO QUE FOI FEITO NA SESSÃO ANTERIOR

| Fase | O Quê | Status |
|------|-------|--------|
| 1 | Análise e reverse engineering | ✅ Completo |
| 2 | Refactoring e remoção de duplicação | ✅ Completo |
| 3 | Minimização de código | ✅ Completo |
| 4-5 | Limpeza agressiva de arquivos | ✅ Completo |
| 6 | Correção de erros de runtime | ✅ Completo |
| 7 | **Descoberta de data contaminada** | ✅ **CRÍTICO** |
| 8 | Data cleaning e retraining | ✅ Completo |
| 9 | Validação biológica | ✅ Completo |
| 10 | Remoção de /train-variants | ✅ Completo |

---

## ⚠️ CUIDADOS

1. **Não toque em trainer.py**: O filtro de dados é crítico
2. **Não remova helpers.py**: Contém RAW_DATA_DIR necessário
3. **Não modifique a lógica de modelo**: Já validada
4. **Frontend é só apresentação**: Toda a lógica pesada está no backend
5. **Teste após cada mudança**: Especialmente CSS/JS

---
