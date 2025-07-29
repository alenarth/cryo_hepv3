let currentPlot = null;
let currentData = null;

async function updatePlot() {
    const payload = {
        cell_type: document.getElementById('cellType').value,
        cryoprotector: document.getElementById('cryoprotector').value
    };

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        currentData = await response.json();
        
        if(currentData.error) {
            alert('Erro: ' + currentData.error);
            return;
        }

        const trace = {
            x: currentData.concentrations,
            y: currentData.viability,
            mode: 'lines+markers',
            name: 'Viabilidade',
            line: {color: '#2196F3', width: 3},
            marker: {size: 8}
        };

        const layout = {
            title: `Relação Concentração-Viabilidade: ${payload.cryoprotector}`,
            xaxis: { title: 'Concentração (%)', gridcolor: '#f0f0f0' },
            yaxis: { title: 'Viabilidade (%)', range: [0, 100] },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white'
        };

        if(currentPlot) {
            Plotly.react('viabilityPlot', [trace], layout);
        } else {
            currentPlot = Plotly.newPlot('viabilityPlot', [trace], layout);
        }

        document.getElementById('optConc').textContent = currentData.optimal.concentration;
        document.getElementById('optViab').textContent = currentData.optimal.value;

    } catch (error) {
        console.error('Erro:', error);
    }
}

async function calculateSpecificViability() {
    const conc = document.getElementById('concentration').value;
    try {
        const response = await fetch('/specific-predict', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                cell_type: document.getElementById('cellType').value,
                cryoprotector: document.getElementById('cryoprotector').value,
                concentration: conc
            })
        });

        const data = await response.json();
        
        if(data.error) {
            alert(data.error);
            return;
        }

        document.getElementById('specificViabilityValue').textContent = data.viability;
        document.getElementById('specificViabilityResult').style.display = 'block';
        
    } catch (error) {
        console.error('Erro:', error);
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('cellType').addEventListener('change', updatePlot);
    document.getElementById('cryoprotector').addEventListener('change', updatePlot);
    document.getElementById('concentration').addEventListener('input', (e) => {
        const value = e.target.value + '%';
        document.getElementById('currentConc').textContent = value;
        document.querySelector('#specificViabilityResult').style.display = 'none';
        document.querySelector('button').innerHTML = `Calcular para ${value}`;
        updatePlot();
    });

    // Inicialização
    updatePlot();
});