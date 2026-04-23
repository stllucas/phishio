from runtime.core.Linguistic import process_text
import re
class TestLinguisticEngine:
    """
    Suíte de testes baseada no Particionamento de Equivalência (EP).
    Divide as entradas em partições válidas (texto normal) e inválidas/limites (vazio, caracteres especiais).
    """

    def test_process_text_standard_url(self):
        text = "http://www.banco-seguro.com.br/login"
        texto_espacado = re.sub(r'[./\-_]', ' ', text)
        result = process_text(texto_espacado)
        assert isinstance(result, list), "O retorno deve ser uma lista de tokens"
        assert "banc" in result, "Stopwords não devem remover palavras essenciais"
        assert "http" not in result, "O protocolo deve ser limpo/ignorado"

    def test_process_text_special_characters(self):
        text = "promoção imperdível!!! ganhe 100% de desconto no pix - acesse já."
        texto_espacado = re.sub(r'[./\-_]', ' ', text)
        result = process_text(texto_espacado)
        assert "!" not in result, "Pontuações devem ser removidas"
        assert "-" not in result, "Hífens isolados devem ser removidos"

    def test_process_text_empty_string(self):
        text = ""
        texto_espacado = re.sub(r'[./\-_]', ' ', text)
        result = process_text(texto_espacado)
        assert result == [], "Uma string vazia deve retornar uma lista vazia"