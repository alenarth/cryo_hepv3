import logging

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
import shap
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import learning_curve, validation_curve
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import Config

logger = logging.getLogger(__name__)

def generate_model_analysis(model: object, X_test: pd.DataFrame, y_test: pd.Series, cell_type: str) -> None:
    """
    Gera análise do modelo e salva gráficos e métricas em HTML.
    Args:
        model (object): Modelo treinado.
        X_test (pd.DataFrame): Dados de teste.
        y_test (pd.Series): Valores reais.
        cell_type (str): Tipo celular.
    Returns:
        None
    """
    # Criar diretório específico para o tipo celular
    graph_dir = Config.GRAPHS_DIR / cell_type
    graph_dir.mkdir(exist_ok=True, parents=True)  # Garante criação recursiva
    # 1. Calcular métricas
    # Converte colunas para float se necessário
    for col in X_test.columns:
        # Normalize: operate on string representation safely to avoid dtype issues
        s = (
            X_test[col]
            .astype(str)
            .fillna("")
            .str.replace('%', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
        )
        mask_invalid = ~s.str.match(r'^-?\d+(\.\d+)?$')
        if mask_invalid.any():
            logger.warning(f"Valores problemáticos em {col}: {X_test[col][mask_invalid].unique()}")
        X_test.loc[:, col] = pd.to_numeric(s, errors='coerce')
    X_test = X_test.astype(float)
    logger.debug('Dtypes após conversão: %s', X_test.dtypes)
    logger.debug('Valores nulos por coluna: %s', X_test.isnull().sum())
    if not pd.api.types.is_numeric_dtype(y_test):
        y_test = (
            y_test
            .astype(str)
            .str.replace('%', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
        )
        y_test = pd.to_numeric(y_test, errors='coerce')
    y_test = y_test.astype(float)
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    # 2. Gerar HTML das métricas (inclui timestamp para verificação)
    from datetime import datetime
    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
    <hr>
    <div class="generated-meta"><small>Gerado em: {generated_at}</small></div>
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
    feature_names = getattr(model, 'feature_names_in_', X_test.columns)
    fig2.add_trace(go.Bar(
        x=feature_names,
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
    # Gráfico 4: SHAP Summary Plot (salva como PNG e HTML)
    shap.summary_plot(shap_values, X_test, show=False)
    plt.tight_layout()
    plt.savefig(str(graph_dir / "shap_summary.png"), bbox_inches='tight')
    plt.close()
    with open(graph_dir / "shap_summary.html", "w", encoding="utf-8") as f:
        f.write('<h3>SHAP Summary Plot</h3><img src="shap_summary.png" style="max-width:100%;">')
    # Gráfico 5: Curva de Aprendizado
    train_sizes, train_scores, test_scores = learning_curve(model, X_test, y_test, cv=5, n_jobs=-1,
                                                           train_sizes=np.linspace(0.1, 1.0, 5))
    train_scores_mean = np.mean(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    plt.figure()
    plt.plot(train_sizes, train_scores_mean, 'o-', color='r', label='Treino')
    plt.plot(train_sizes, test_scores_mean, 'o-', color='g', label='Validação')
    plt.title('Curva de Aprendizado')
    plt.xlabel('Tamanho do Treino')
    plt.ylabel('Score')
    plt.legend(loc='best')
    plt.tight_layout()
    plt.savefig(str(graph_dir / "learning_curve.png"), bbox_inches='tight')
    plt.close()
    with open(graph_dir / "learning_curve.html", "w", encoding="utf-8") as f:
        f.write('<h3>Curva de Aprendizado</h3><img src="learning_curve.png" style="max-width:100%;">')
    # Gráfico 6: Curva de Validação para max_depth
    param_range = np.arange(1, 11)
    train_scores, test_scores = validation_curve(model, X_test, y_test, param_name="max_depth",
                                                param_range=param_range, cv=5, n_jobs=-1)
    train_scores_mean = np.mean(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    plt.figure()
    plt.plot(param_range, train_scores_mean, label="Treino", color="r")
    plt.plot(param_range, test_scores_mean, label="Validação", color="g")
    plt.title("Curva de Validação: max_depth")
    plt.xlabel("max_depth")
    plt.ylabel("Score")
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(str(graph_dir / "validation_curve.png"), bbox_inches='tight')
    plt.close()
    with open(graph_dir / "validation_curve.html", "w", encoding="utf-8") as f:
        f.write('<h3>Curva de Validação (max_depth)</h3><img src="validation_curve.png" style="max-width:100%;">')
    # Gráfico 7: Residual Plot
    plt.figure()
    plt.scatter(y_pred, errors, alpha=0.7, color='#009688')
    plt.axhline(0, color='red', linestyle='--')
    plt.title('Residual Plot')
    plt.xlabel('Valor Previsto')
    plt.ylabel('Resíduo (Real - Previsto)')
    plt.tight_layout()
    plt.savefig(str(graph_dir / "residual_plot.png"), bbox_inches='tight')
    plt.close()
    with open(graph_dir / "residual_plot.html", "w", encoding="utf-8") as f:
        f.write('<h3>Residual Plot</h3><img src="residual_plot.png" style="max-width:100%;">')




    return metrics_path