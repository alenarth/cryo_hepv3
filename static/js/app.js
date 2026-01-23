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
    'TREHALOSE': Array.from({length: 21}, (_, i) => i * 5),
    'BOTH': Array.from({length: 21}, (_, i) => i * 5)
};

// Mapeamento de rótulos, populado a partir da configuração injetada na template
const CP_LABELS = (typeof AppConfig !== 'undefined' && AppConfig.CRYOPROTECTORS) ? Object.fromEntries(AppConfig.CRYOPROTECTORS) : {};

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
        const cpLabel = CP_LABELS[payload.cryoprotector] || payload.cryoprotector;
        const layout = {
            title: `Relação Concentração-Viabilidade: ${cpLabel}`,
            xaxis: { title: 'Concentração (%)', gridcolor: '#f0f0f0' },
            yaxis: { title: 'Viabilidade (%)', range: [0, 100] },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            autosize: true,
            margin: { t: 60, r: 30, l: 60, b: 60 }
        };
        Plotly.newPlot('viabilityPlot', [trace], layout, {responsive: true, displayModeBar: false}).then(() => {
            hideSpinner();
            document.getElementById('downloadPlotBtn').classList.add('show');
        });
        document.getElementById('optConc').textContent = currentData.optimal.concentration;
        document.getElementById('optViab').textContent = currentData.optimal.value.toFixed(2);
        // Mostrar variante do modelo se disponível
        const mvEl = document.getElementById('modelVariant');
        if (currentData.model_variant && mvEl) {
            mvEl.textContent = `(${currentData.model_variant})`;
            mvEl.classList.remove('d-none');
        } else if (mvEl) {
            mvEl.classList.add('d-none');
        }
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
    const cp = document.getElementById('cryoprotector').value.toUpperCase();
    const cellType = document.getElementById('cellType').value;
    // Caso BOTH: ler seleção de par e chamar /predict-both
    if (cp === 'BOTH') {
        const sel = document.getElementById('pairSelect');
        if (!sel) {
            alert('Nenhuma combinação selecionada.');
            return;
        }
        const [d, t] = sel.value.split('_').map(Number);
        try {
            const resp = await fetch('/predict-both', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({cell_type: cellType, dmso: d, trehalose: t})
            });
            const js = await resp.json();
            if (js.errors || js.error) {
                alert((js.errors || js.error || 'Erro desconhecido'));
                return;
            }
            document.getElementById('specificViabilityValue').textContent = js.viability.toFixed(2);
            document.getElementById('specificViabilityResult').classList.add('show');
        } catch (err) {
            console.error('Erro:', err);
        }
        return;
    }

    // Caso normal
    const concEl = document.getElementById('concentration');
    const conc = concEl ? concEl.value : null;
    try {
        const response = await fetch('/specific-predict', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                cell_type: cellType,
                cryoprotector: document.getElementById('cryoprotector').value,
                concentration: conc
            })
        });
        const data = await response.json();
        if(data.error) {
            alert(data.error);
            return;
        }
        document.getElementById('specificViabilityValue').textContent = data.viability.toFixed(2);
        document.getElementById('specificViabilityResult').classList.add('show');
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
        // Remove qualquer input/note antigo
        if (concentrationInput) concentrationInput.remove();
        const existingNote = document.getElementById('combosNote');
        if (existingNote) existingNote.remove();
        const existingPairSelect = document.getElementById('pairSelect');
        if (existingPairSelect) existingPairSelect.remove();

        if (cp === 'BOTH') {
            // Para BOTH não usamos um slider: a curva será gerada a partir das combinações no dataset
            let note = document.createElement('div');
            note.id = 'combosNote';
            note.className = 'small text-muted';
            note.textContent = 'Escolha uma combinação disponível para cálculo específico.';
            currentConcSpan.parentNode.insertBefore(note, currentConcSpan.parentNode.firstChild.nextSibling);
            currentConcSpan.textContent = '—';
            // Buscar combinações via API
            fetch(`/available-both/${encodeURIComponent(cellTypeSelect.value)}`).then(r => r.json()).then(js => {
                if (js && js.pairs && js.pairs.length) {
                    let sel = document.createElement('select');
                    sel.id = 'pairSelect';
                    sel.className = 'form-select mb-2';
                    js.pairs.forEach(p => {
                        const opt = document.createElement('option');
                        opt.value = `${p.dmso}_${p.trehalose}`;
                        opt.textContent = p.label;
                        sel.appendChild(opt);
                    });
                    currentConcSpan.parentNode.insertBefore(sel, currentConcSpan.parentNode.firstChild.nextSibling);
                    // Habilita o botão
                    if (calcButton) {
                        calcButton.disabled = false;
                    }
                    // Quando mudar seleção, atualiza o display
                    sel.addEventListener('change', () => {
                        const [d, t] = sel.value.split('_');
                        currentConcSpan.textContent = `${d}% + ${t}%`;
                    });
                    // Inicializa com a primeira
                    const first = js.pairs[0];
                    currentConcSpan.textContent = `${first.dmso}% + ${first.trehalose}%`;
                } else {
                    // Nenhuma combinação: informar e desativar botão
                    const noteEmpty = document.createElement('div');
                    noteEmpty.className = 'small text-muted';
                    noteEmpty.id = 'combosNoteEmpty';
                    noteEmpty.textContent = 'Nenhuma combinação disponível no dataset; o gráfico usará o grid padrão.';
                    currentConcSpan.parentNode.insertBefore(noteEmpty, currentConcSpan.parentNode.firstChild.nextSibling);
                    if (calcButton) {
                        calcButton.disabled = true;
                    }
                }
                // Atualiza o gráfico
                updatePlotDebounced();
            }).catch(err => {
                console.error('Erro ao buscar combos:', err);
                updatePlotDebounced();
            });
            // Não cria slider
            return;
        }

        // Caso normal: cria o slider
        const values = CONCENTRATION_RANGES[cp] || CONCENTRATION_RANGES['DMSO'];
        let newInput = document.createElement('input');
        newInput.type = 'range';
        newInput.id = 'concentration';
        newInput.className = 'form-range';
        newInput.min = Math.min(...values);
        newInput.max = Math.max(...values);
        newInput.step = 5;
        newInput.value = values[0];
        currentConcSpan.parentNode.insertBefore(newInput, currentConcSpan.parentNode.firstChild.nextSibling);
        concentrationInput = newInput;
        concentrationInput.addEventListener('input', handleConcentrationChange);
        concentrationInput.addEventListener('change', handleConcentrationChange);
        // Reativa o botão de cálculo específico
        if (calcButton) {
            calcButton.disabled = false;
        }
        handleConcentrationChange();
    }

    function handleConcentrationChange(e) {
        let value = concentrationInput.value + '%';
        currentConcSpan.textContent = value;
        document.querySelector('#specificViabilityResult').classList.remove('show');
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