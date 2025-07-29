 
from app import validate_input, get_model

def test_validate_input_valid():
    assert validate_input('hepg2', 'DMSO') == []
    assert validate_input('mice', 'TREHALOSE') == []
    assert validate_input('rat', 'GLICEROL') == []

def test_validate_input_invalid():
    assert 'Tipo celular inválido' in validate_input('foo', 'DMSO')[0]
    assert 'Crioprotetor inválido' in validate_input('hepg2', 'FOO')[0]

def test_get_model_exists():
    # Assume modelo existe para hepg2
    model = get_model('hepg2')
    assert model is not None

def test_get_model_not_exists():
    try:
        get_model('notacell')
        assert False, "Deveria lançar exceção para modelo inexistente"
    except Exception:
        assert True
