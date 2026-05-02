import pytest
import time
from typing import Final
from runtime.core.SearchEngine import SearchEngine


# O limiar de alerta mínimo para classificar como "suspicious" definido no main.py.
LIMIAR_ALERTA: Final[float] = 0.40


class Cronometro:
    """Context manager utilitário para medir o tempo de processamento padrão."""

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        self.tempo_processamento = time.time() - self.start_time


@pytest.fixture(scope="module")
def engine():
    return SearchEngine()


def test_cosine_similarity_ranking(engine):
    texto_teste = "ganhe iphone gratis clique aqui promocao"

    with Cronometro() as cronometro:
        vetor = engine.gerar_vetor_consulta_tfidf(texto_teste)
        assert isinstance(
            vetor, dict), "O vetor gerado deve ser um dicionário (termos -> tf-idf)"
        resultados = engine.ranquear_documentos_completo(vetor)

    assert isinstance(
        resultados, list), "O resultado do ranqueamento deve ser uma lista"

    print("\n--- Resultado da Análise de Ranqueamento de Cosseno ---")
    print(
        f"Tempo de Processamento: {cronometro.tempo_processamento:.4f} segundos")
    print(f"Documentos Candidatos Retornados: {len(resultados)}")
    print(f"Limiar de Alerta Configurado: {LIMIAR_ALERTA}")

    if resultados:
        assert isinstance(
            resultados[0], tuple), "Cada resultado deve ser uma tupla (doc_id, score)"
        assert 0.0 <= resultados[0][1] <= 1.0, "O score da similaridade de cosseno deve estar entre 0 e 1"
        maior_score = resultados[0][1]
        print(f"Score Máximo Encontrado (Cosseno): {maior_score:.4f}")


def test_busca_paginada(engine):
    with Cronometro() as cronometro:
        resultados, total = engine.buscar(
            "gratis", pagina=1, resultados_por_pagina=5)

    assert isinstance(resultados, list)
    assert len(
        resultados) <= 5, "A paginação não pode retornar mais itens que o limite da página."

    print("\n--- Resultado da Busca Paginada ---")
    print(
        f"Tempo de Processamento: {cronometro.tempo_processamento:.4f} segundos")
    print(
        f"Documentos Candidatos Retornados (Página): {len(resultados)} de um total de {total}")
    print(f"Limiar de Alerta Configurado: {LIMIAR_ALERTA}")

    if resultados:
        maior_score = resultados[0].get('score') if isinstance(
            resultados[0], dict) else resultados[0][1]
        print(f"Score Máximo Encontrado (Cosseno): {maior_score:.4f}")


def test_cenario_a_linkedin(engine):
    """
    Cenário A: Identificação de Conteúdo Benigno (Verdadeiro Negativo).
    Testa a estabilidade do sistema ao processar páginas com alta densidade de conteúdo como o LinkedIn.
    """
    url_teste = "https://www.linkedin.com/"
    # Simula conteúdo extraído de redes sociais corporativas
    conteudo_benigno = "linkedin rede social profissional vagas de emprego recrutamento conexões networking tecnologia carreira"

    with Cronometro() as cronometro:
        vetor = engine.gerar_vetor_consulta_tfidf(conteudo_benigno)
        resultados = engine.ranquear_documentos_completo(vetor)

    print(f"\n--- Resultado da Análise Cenário A ({url_teste}) ---")
    print(
        f"Tempo de Processamento: {cronometro.tempo_processamento:.4f} segundos")
    print(f"Documentos Candidatos Retornados: {len(resultados)}")
    print(f"Limiar de Alerta Configurado: {LIMIAR_ALERTA}")

    if resultados:
        maior_score = resultados[0][1]
        print(f"Score Máximo Encontrado (Cosseno): {maior_score:.4f}")
        assert maior_score < LIMIAR_ALERTA, f"Falso Positivo: O score {maior_score} excedeu o limiar de {LIMIAR_ALERTA}"
