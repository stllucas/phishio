"""Módulo central para recursos de Processamento de Linguagem Natural (PLN)."""
import re
from logging import getLogger

import nltk
from bs4 import BeautifulSoup

logger = getLogger('ColetorLogger')

try:
    nltk.data.find('corpora/stopwords')
except nltk.downloader.DownloadError:
    nltk.download('stopwords', quiet=True)

try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt', quiet=True)

STOPWORDS = set(nltk.corpus.stopwords.words('portuguese')) | {"http", "https", "www", "com", "br", "net", "org", "gov", "edu"}
STEMMER = nltk.stem.SnowballStemmer("portuguese")


def process_text(conteudo_html: str) -> list[str]:
    """Aplica análise léxica completa: limpeza de HTML, tokenização, remoção de stopwords e stemming."""
    try:
        soup = BeautifulSoup(conteudo_html, 'html.parser')
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        texto_limpo = soup.get_text(separator=' ')
    except Exception as e:
        logger.error(f"Erro na BeautifulSoup ao processar HTML. {e}")
        texto_limpo = ""

    texto_espacado = re.sub(r'[./\-_]', ' ', texto_limpo)

    limpo = re.sub(
        r'[^a-zA-ZáéíóúàèìòùãõâêîôûçÁÉÍÓÚÀÈÌÒÙÃÕÂÊÎÔÛÇ\s]', '', texto_espacado).lower()
    tokens = limpo.split()

    return [STEMMER.stem(token) for token in tokens if token not in STOPWORDS and len(token) > 2]
