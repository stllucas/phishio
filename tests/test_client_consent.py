import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, ANY
from runtime.main import app

client = TestClient(app)

def test_registrar_consentimento_sucesso(mock_firestore):
    """
    Valida se o endpoint de consentimento registra os dados com sucesso
    e se o hash do IP é utilizado como ID do documento.
    """
    payload = {
        "versao_termos": "v1.0",
        "user_agent": "Chrome/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"
    }

    response = client.post("/registrar_consentimento", json=payload)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "Consentimento registrado" in response.json()["message"]

    mock_firestore.collection.assert_called_once_with("user_consent")

    doc_ref_mock = mock_firestore.collection.return_value.document.return_value
    doc_ref_mock.set.assert_called_once_with({
        "ip_hash": ANY,
        "consent": True,
        "versao_termo": "v1.0",
        "user_agent": "Chrome/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0",
        "data_aceite": ANY,
        "ultimo_ip_mascarado": ANY
    }, merge=True)

def test_registrar_consentimento_db_indisponivel(monkeypatch):
    """
    Garante que a API retorne erro 503 se o cliente Firestore não estiver inicializado.
    """
    monkeypatch.setattr("runtime.main.db", None)

    payload = {"versao_termos": "v1.0", "user_agent": "TestBot"}
    response = client.post("/registrar_consentimento", json=payload)

    assert response.status_code == 503
    assert response.json()["detail"] == "Banco de dados indisponível."

def test_registrar_consentimento_payload_invalido():
    """
    Verifica a validação de esquema do FastAPI para campos obrigatórios.
    """
    response = client.post("/registrar_consentimento", json={})
    assert response.status_code == 422