import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
import shap
from sklearn.metrics import mean_squared_error, r2_score
import joblib
from config import Config

def generate_model_analysis(model, X_test, y_test, cell_type: str):
    """Gera análise completa do modelo"""
    # Criar diretório específico para o tipo celular
    graph_dir = Config.GRAPHS_DIR / cell_type
    graph_dir.mkdir(exist_ok=True, parents=True)  # Garante criação recursiva
    
    # 1. Calcular métricas
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    # 2. Gerar HTML das métricas
    metrics_html = f"""
    <div class="metrics-grid">
        <div class="metric-card bg-primary">
            <h5>RMSE</h5>
            <div class="value">{rmse:.2f}</div>
            <small>Raiz do Erro Quadrático Médio</small>
        </div>
        <div class="metric-card bg-success">
            <h5>R²</h5>
            <div class="value">{r2:.2f}</div>
            <small>Coeficiente de Determinação</small>
        </div>
    </div>
    """
    
    # 3. Salvar arquivo de métricas
    metrics_path = graph_dir / "metrics.html"
    with open(metrics_path, "w", encoding="utf-8") as f:
        f.write(metrics_html)
    
    # Gráfico 1: Valores Reais vs. Previstos
    fig1 = make_subplots(rows=1, cols=1)
    fig1.add_trace(go.Scatter(
        x=y_test,
        y=y_pred,
        mode='markers',
        marker=dict(color='#2196F3', size=8),
        name='Amostras'
    ))
    fig1.add_trace(go.Scatter(
        x=[y_test.min(), y_test.max()],
        y=[y_test.min(), y_test.max()],
        mode='lines',
        line=dict(color='#FF5252', dash='dash'),
        name='Linha Perfeita'
    ))
    fig1.update_layout(
        title='Valores Reais vs. Previstos',
        xaxis_title='Valor Real (% Queda)',
        yaxis_title='Valor Previsto (% Queda)',
        template='plotly_white'
    )
    fig1.write_html(str(graph_dir / "real_vs_predicted.html"), include_plotlyjs='cdn')
    
    # Gráfico 2: Importância de Features com SHAP
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=model.feature_names_in_,
        y=np.abs(shap_values).mean(0),
        marker_color='#4CAF50',
        name='Importância SHAP'
    ))
    fig2.update_layout(
        title='Impacto Médio das Variáveis (SHAP)',
        xaxis_title='Variáveis',
        yaxis_title='Valor SHAP Médio',
        template='plotly_white'
    )
    fig2.write_html(str(graph_dir / "shap_importance.html"), include_plotlyjs='cdn')
    
    # Gráfico 3: Distribuição de Erros
    errors = y_test - y_pred
    fig3 = go.Figure()
    fig3.add_trace(go.Histogram(
        x=errors,
        marker_color='#7E57C2',
        opacity=0.75,
        name='Distribuição de Erros'
    ))
    fig3.update_layout(
        title='Distribuição dos Erros de Predição',
        xaxis_title='Erro (Real - Previsto)',
        yaxis_title='Contagem',
        template='plotly_white'
    )
    fig3.write_html(str(graph_dir / "error_distribution.html"), include_plotlyjs='cdn')
    
    return metrics_html