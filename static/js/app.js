// Spinner overlay control
function showSpinner() {
    document.getElementById('plotSpinner').classList.remove('d-none');
    document.getElementById('downloadPlotBtn').style.display = 'none';
}

function hideSpinner() {
    document.getElementById('plotSpinner').classList.add('d-none');
}

let currentPlot = null;
let currentData = null;
let debounceTimeout = null;
const CONCENTRATION_RANGES = {
    'DMSO': Array.from({length: 21}, (_, i) => i * 5),
    'TREHALOSE': [0, 0.97, 1.94, 3.88, 7.77, 15.54, 31.08, 62.16, 100]
};

function updatePlotDebounced() {
    if (debounceTimeout) clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(updatePlot, 300);
}

async function updatePlot() {
    const payload = {
        cell_type: document.getElementById('cellType').value,
        cryoprotector: document.getElementById('cryoprotector').value
    };
    showSpinner();
    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        currentData = await response.json();
        if(currentData.error) {
            alert('Erro: ' + currentData.error);
            hideSpinner();
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
            paper_bgcolor: 'white',
            autosize: true,
            margin: { t: 60, r: 30, l: 60, b: 60 }
        };
        Plotly.newPlot('viabilityPlot', [trace], layout, {responsive: true, displayModeBar: false}).then(() => {
            hideSpinner();
            document.getElementById('downloadPlotBtn').style.display = 'inline-block';
        });
        document.getElementById('optConc').textContent = currentData.optimal.concentration;
        document.getElementById('optViab').textContent = currentData.optimal.value;
    } catch (error) {
        hideSpinner();
        console.error('Erro:', error);
    }
}

// Download button handler (fora da função updatePlot)
document.addEventListener('DOMContentLoaded', () => {
    const downloadBtn = document.getElementById('downloadPlotBtn');
    if (downloadBtn) {
        downloadBtn.onclick = function() {
            Plotly.downloadImage(document.getElementById('viabilityPlot'), {format: 'png', filename: 'grafico_viabilidade'});
        };
    }
});

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

document.addEventListener('DOMContentLoaded', () => {
    const cellTypeSelect = document.getElementById('cellType');
    const cryoprotectorSelect = document.getElementById('cryoprotector');
    let concentrationInput = document.getElementById('concentration');
    const currentConcSpan = document.getElementById('currentConc');
    const calcButton = document.querySelector('button');

    function updateConcentrationInput() {
        const cp = cryoprotectorSelect.value.toUpperCase();
        const values = CONCENTRATION_RANGES[cp] || CONCENTRATION_RANGES['DMSO'];
        // Remove input antigo
        if (concentrationInput) concentrationInput.remove();
        let newInput;
        if (cp === 'TREHALOSE') {
            newInput = document.createElement('select');
            newInput.id = 'concentration';
            newInput.className = 'form-select';
            values.forEach(v => {
                const opt = document.createElement('option');
                opt.value = v;
                opt.textContent = v + '%';
                newInput.appendChild(opt);
            });
        } else {
            newInput = document.createElement('input');
            newInput.type = 'range';
            newInput.id = 'concentration';
            newInput.className = 'form-range';
            newInput.min = Math.min(...values);
            newInput.max = Math.max(...values);
            newInput.step = 5;
            newInput.value = values[0];
        }
        currentConcSpan.parentNode.insertBefore(newInput, currentConcSpan.parentNode.firstChild.nextSibling);
        concentrationInput = newInput;
        concentrationInput.addEventListener('input', handleConcentrationChange);
        concentrationInput.addEventListener('change', handleConcentrationChange);
        handleConcentrationChange();
    }

    function handleConcentrationChange(e) {
        let value = concentrationInput.value;
        if (cryoprotectorSelect.value.toUpperCase() === 'TREHALOSE') {
            value = value;
        } else {
            value = value + '%';
        }
        currentConcSpan.textContent = value;
        document.querySelector('#specificViabilityResult').style.display = 'none';
        calcButton.innerHTML = `Calcular para ${value}`;
        updatePlotDebounced();
    }

    cellTypeSelect.addEventListener('change', updatePlotDebounced);
    cryoprotectorSelect.addEventListener('change', () => {
        updateConcentrationInput();
        updatePlotDebounced();
    });

    // Inicialização
    updateConcentrationInput();
    updatePlot();
});