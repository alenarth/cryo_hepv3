 
from app import validate_input, get_model, app

def test_validate_input_valid():
    assert validate_input('hepg2', 'DMSO') == []
    assert validate_input('mice', 'TREHALOSE') == []
    assert validate_input('rat', 'TREHALOSE') == []

def test_validate_input_invalid():
    assert 'Tipo celular inválido' in validate_input('foo', 'DMSO')[0]
    assert 'Crioprotetor inválido' in validate_input('hepg2', 'FOO')[0]

def test_get_model_exists(monkeypatch):
    # Simula joblib.load retornando um modelo simples
    class DummyModel:
        def predict(self, X):
            return [10]
    monkeypatch.setattr('joblib.load', lambda path: DummyModel())
    model = get_model('hepg2')
    assert hasattr(model, 'predict')


def test_get_model_case_insensitive(monkeypatch):
    class DummyModel:
        def predict(self, X):
            return [10]
    monkeypatch.setattr('joblib.load', lambda path: DummyModel())
    model = get_model('HEPG2')
    assert hasattr(model, 'predict')


def test_get_model_not_exists():
    import pytest
    with pytest.raises(FileNotFoundError):
        get_model('notacell')


def test_model_metrics_case_insensitive(monkeypatch):
    class DummyModel:
        feature_importances_ = [0.1, 0.2, 0.7]
        n_features_in_ = 5
    monkeypatch.setattr('joblib.load', lambda path: DummyModel())
    client = app.test_client()
    resp = client.get('/model-metrics/HEPG2')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'feature_importances' in data and 'n_features_in' in data
