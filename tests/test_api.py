import time
from fastapi.testclient import TestClient
from runtime.main import app

client = TestClient(app)


def test_api_performance_and_accuracy():
    """
    Testes de Integração de Sistemas: Foco no comportamento geral e nos recursos não funcionais (Performance).
    """
    client.post("/check_url", json={"url": "http://warmup.com", "dom": "<html></html>"})
    
    start_time = time.time()

    payload = {
        "url": "https://blog.megajogos.com.br/comoganhar-creditos-gratis-megajogos/",
        "dom": "<html><body>Como ganhar créditos grátis no MegaJogos</body></html>",
    }

    response = client.post("/check_url", json=payload)

    end_time = time.time()
    execution_time_ms = (end_time - start_time) * 1000

    assert response.status_code == 200, (
        f"A API falhou com status: {response.status_code} - {response.text}"
    )

    data = response.json()
    assert "score" in data, "A resposta deve conter o ranqueamento do cosseno"

    assert execution_time_ms < 500, (
        f"Performance ruim: A API demorou {execution_time_ms:.2f}ms"
    )
