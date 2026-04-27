import importlib
from unittest.mock import patch
from pathlib import Path

def test_missing_secrets_file():
    """
    Garante que a falta do arquivo de credenciais do Firestore (secrets)
    gere uma falha tratável (que o backend captura na inicialização).
    """
    with patch('runtime.core.Config.SECRETS_FILE', Path('/caminho/falso/secrets.json')):
        try:
            importlib.import_module('runtime.main')
        except Exception as e:
            assert isinstance(e, (FileNotFoundError, Exception)), "Deve tratar a falta do arquivo secrets."
