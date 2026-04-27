import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture(autouse=True)
def mock_firestore(monkeypatch):
    """
    Mock global do Firestore para todos os testes.
    Evita o erro 'Event loop is closed' ao usar o TestClient do FastAPI
    e impede que os testes consumam cota real do Google Cloud (gRPC).
    """
    mock_db = MagicMock()

    mock_doc = MagicMock()
    mock_doc.exists = False

    mock_db.collection.return_value.add = AsyncMock()

    doc_ref_mock = mock_db.collection.return_value.document.return_value
    doc_ref_mock.get = AsyncMock(return_value=mock_doc)
    doc_ref_mock.set = AsyncMock()
    doc_ref_mock.update = AsyncMock()

    monkeypatch.setattr("runtime.main.db", mock_db)
    return mock_db
