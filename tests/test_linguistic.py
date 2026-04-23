import pytest
from runtime.core.Linguistic import process_text

class TestLinguisticEngine:
    """
    Suíte de testes baseada no Particionamento de Equivalência (EP).
    Divide as entradas em partições válidas (texto normal) e inválidas/limites (vazio, caracteres especiais).
    """

    def test_process_text_standard_url(self):
        text = "http://www.banco-seguro.com.br/login"
        result = process_text(text)
        assert isinstance(result, list), "O retorno deve ser uma lista de tokens"
        assert "banco" in result, "Stopwords não devem remover palavras essenciais"
        assert "http" not in result, "O protocolo deve ser limpo/ignorado"

    def test_process_text_special_characters(self):
        text = "promoção imperdível!!! ganhe 100% de desconto no pix - acesse já."
        result = process_text(text)
        assert "!" not in result, "Pontuações devem ser removidas"
        assert "-" not in result, "Hífens isolados devem ser removidos"

    def test_process_text_empty_string(self):
        text = ""
        result = process_text(text)
        assert result == [], "Uma string vazia deve retornar uma lista vazia"