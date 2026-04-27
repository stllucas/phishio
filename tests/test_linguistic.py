from runtime.core.Linguistic import process_text
import re
import nltk


class TestLinguisticEngine:
    def test_process_text_standard_url(self):
        text = "http://www.banco-seguro.com.br/login"
        texto_espacado = re.sub(r'[./\-_]', ' ', text)
        result = process_text(texto_espacado)
        assert isinstance(
            result, list), "O retorno deve ser uma lista de tokens"
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

    def test_process_text_weird_languages(self):
        text = "这是一个中文字符串 - проверка кириллицы - arabic script العربية"
        texto_espacado = re.sub(r'[./\-_]', ' ', text)
        result = process_text(texto_espacado)
        assert isinstance(
            result, list), "O processamento não deve quebrar com caracteres estrangeiros."

    def test_nltk_resources_loaded(self):
        try:
            nltk.data.find('corpora/stopwords')
            nltk.data.find('tokenizers/punkt')
            loaded = True
        except LookupError:
            loaded = False
        assert loaded, "Os recursos do NLTK (stopwords e punkt) precisam estar baixados e acessíveis."
