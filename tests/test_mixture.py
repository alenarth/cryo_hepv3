import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_predict_mixture_valid(client):
    resp = client.post('/predict-mixture', json={
        "cell_type": "hepg2",
        "mixture": [
            {"cryoprotector": "DMSO", "concentration": 10},
            {"cryoprotector": "TREHALOSE", "concentration": 5}
        ]
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert "viability" in data
    assert 0 <= data["viability"] <= 100

def test_predict_mixture_invalid_cell_type(client):
    resp = client.post('/predict-mixture', json={
        "cell_type": "banana",
        "mixture": [
            {"cryoprotector": "DMSO", "concentration": 10},
            {"cryoprotector": "TREHALOSE", "concentration": 5}
        ]
    })
    assert resp.status_code == 400
    data = resp.get_json()
    assert "errors" in data

def test_predict_mixture_invalid_cryoprotectors(client):
    resp = client.post('/predict-mixture', json={
        "cell_type": "hepg2",
        "mixture": [
            {"cryoprotector": "DMSO", "concentration": 10},
            {"cryoprotector": "BANANA", "concentration": 5}
        ]
    })
    assert resp.status_code == 400
    data = resp.get_json()
    assert "errors" in data

def test_predict_mixture_too_few(client):
    resp = client.post('/predict-mixture', json={
        "cell_type": "hepg2",
        "mixture": [
            {"cryoprotector": "DMSO", "concentration": 10}
        ]
    })
    assert resp.status_code == 400
    data = resp.get_json()
    assert "errors" in data
