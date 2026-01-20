window.downloadGraph = function(cellType, plotName) {
    const url = `/static/graphs/${cellType}/${plotName}.png`;
    const link = document.createElement('a');
    link.href = url;
    link.download = `${plotName}_${cellType}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};