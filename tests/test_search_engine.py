import pytest
from runtime.core.SearchEngine import SearchEngine

@pytest.fixture(scope="module")
def engine():
    return SearchEngine()

def test_cosine_similarity_ranking(engine):
    texto_teste = "ganhe iphone gratis clique aqui promocao"
    
    vetor = engine.gerar_vetor_consulta_tfidf(texto_teste)
    assert isinstance(vetor, dict), "O vetor gerado deve ser um dicionário (termos -> tf-idf)"
    
    resultados = engine.ranquear_documentos_completo(vetor)
    assert isinstance(resultados, list), "O resultado do ranqueamento deve ser uma lista"
    
    if resultados:
        assert isinstance(resultados[0], tuple), "Cada resultado deve ser uma tupla (doc_id, score)"
        assert 0.0 <= resultados[0][1] <= 1.0, "O score da similaridade de cosseno deve estar entre 0 e 1"