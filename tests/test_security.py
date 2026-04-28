from fastapi.testclient import TestClient
from runtime.main import app

client = TestClient(app)


def test_sql_nosql_injection():
    payload = {
        "url": "http://example.com/login?user={'$gt': ''}",
        "dom": "<html> test injection </html>"
    }
    response = client.post("/check_url", json=payload)
    assert response.status_code in [
        200, 422], "O sistema não deve quebrar (500) com caracteres de escape."


def test_payload_ddos_dom():
    large_dom = "A" * 5 * 1024 * 1024
    payload = {
        "url": "http://example.com/huge",
        "dom": large_dom
    }
    response = client.post("/check_url", json=payload)
    assert response.status_code != 500, "O servidor não pode retornar 500 por estouro de memória/payload."


def test_malformed_url():
    payload = {
        "url": "javascript:alert(1)",
        "dom": "<html>xss</html>"
    }
    response = client.post("/check_url", json=payload)
    assert response.status_code != 500, "URLs malformadas ou com protocolos perigosos não devem causar falha interna."


def test_headers_exposure():
    response = client.get("/openapi.json")
    headers = response.headers

    assert "x-powered-by" not in headers.keys()
    assert "server" not in headers.keys() or headers["server"] != "uvicorn"
