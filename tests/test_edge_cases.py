import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from runtime.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_empty_dom():
    payload = {"url": "http://site.com", "dom": ""}
    response = client.post("/check_url", json=payload)

    assert response.status_code == 200
    assert response.json().get(
        "status") == "needs_content", "DOM vazio deve engatilhar a requisição de conteúdo."


def test_null_dom():
    payload = {"url": "http://site.com", "dom": None}
    response = client.post("/check_url", json=payload)

    assert response.status_code in [200, 422]


@pytest.mark.asyncio
async def test_concurrency():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        payload = {"url": "http://concorrencia.com",
                   "dom": "<html>Teste Concorrente</html>"}
        tasks = [ac.post("/check_url", json=payload) for _ in range(10)]
        responses = await asyncio.gather(*tasks)

        for response in responses:
            assert response.status_code == 200, "Requisições simultâneas não devem travar o banco ou a API."
