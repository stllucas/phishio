import time
from fastapi.testclient import TestClient
from runtime.main import app

client = TestClient(app)

def test_handshake_flow_complete():
    payload_handshake = {"url": "http://site-desconhecido.com/login"}
    response1 = client.post("/check_url", json=payload_handshake)
    
    assert response1.status_code == 200
    assert response1.json().get("status") == "needs_content", "Deveria solicitar o DOM (needs_content)."
    
    payload_full = {
        "url": "http://site-desconhecido.com/login",
        "dom": "<html><body>Faça login no seu banco seguro!</body></html>"
    }
    response2 = client.post("/check_url", json=payload_full)
    
    assert response2.status_code == 200
    data = response2.json()
    assert "score" in data, "A resposta deve conter o score da análise."
    assert data["status"] in ["safe", "suspicious", "phishing"], "O status deve ser um veredito válido."

def test_cache_persistence_performance():
    payload = {"url": "http://site-cache.com", "dom": "<html>safe content</html>"}
    
    res1 = client.post("/check_url", json=payload)
    res2 = client.post("/check_url", json=payload)
    
    assert res1.status_code == 200
    assert res2.status_code == 200

def test_false_positive_google():
    payload = {"url": "https://www.google.com", "dom": "<html><body>Pesquisa Google, Estou com sorte</body></html>"}
    response = client.post("/check_url", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "safe", "Sites legítimos e conhecidos devem ser classificados como seguros."
