document.addEventListener('DOMContentLoaded', () => {
    const modelSelector = document.getElementById('modelSelector');
    let currentPlots = {};

    async function updateAnalysis() {
        const cellType = modelSelector.value;
        
        try {
            // Carregar métricas
            const metricsResponse = await fetch(`/graphs/${cellType}/metrics.html`);
            document.getElementById('metrics').innerHTML = await metricsResponse.text();

            // Carregar gráficos
            await loadPlot(cellType, 'real_vs_predicted', 'realVsPredictedPlot');
            await loadPlot(cellType, 'shap_importance', 'shapImpactPlot');
            await loadPlot(cellType, 'error_distribution', 'errorDistributionPlot');

        } catch (error) {
            console.error('Erro:', error);
        }
    }

    async function loadPlot(cellType, plotName, containerId) {
        try {
            const response = await fetch(`/model-analysis/${cellType}/${plotName}`);
            const html = await response.text();
            
            // Usar iframe para renderização confiável
            const container = document.getElementById(containerId);
            container.innerHTML = `
                <iframe 
                    srcdoc="${html.replace(/"/g, '&quot;')}" 
                    style="width: 100%; height: 500px; border: none;"
                ></iframe>
            `;

        } catch (error) {
            console.error(`Erro no gráfico ${plotName}:`, error);
            document.getElementById(containerId).innerHTML = `
                <div class="alert alert-danger">
                    Gráfico não disponível: ${error.message}
                </div>
            `;
        }
    }

    function showErrorAlert() {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            Falha ao carregar dados. Verifique:
            <ul>
                <li>Modelos foram treinados corretamente</li>
                <li>Arquivos de análise existem</li>
                <li>Conexão com o servidor</li>
            </ul>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.container').prepend(alert);
    }

    // Event Listeners
    modelSelector.addEventListener('change', updateAnalysis);
    updateAnalysis();
});