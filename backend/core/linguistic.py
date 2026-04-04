# ==============================================================================
# backend/core/linguistic.py
# Módulo central para recursos de Processamento de Linguagem Natural (PLN).
# ==============================================================================
import nltk
import re
import warnings
from bs4 import BeautifulSoup
from logging import getLogger

# Configuração do Logger
logger = getLogger('ColetorLogger')

# Baixa os recursos do NLTK de forma segura
try:
    nltk.data.find('corpora/stopwords')
except nltk.downloader.DownloadError:
    nltk.download('stopwords', quiet=True)

try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt', quiet=True)

# Define recursos de Processamento de Linguagem Natural (PLN)
STOPWORDS = set(nltk.corpus.stopwords.words('portuguese'))
STEMMER = nltk.stem.SnowballStemmer("portuguese")

def process_text(conteudo_html: str) -> list[str]:
    """Aplica análise léxica completa: limpeza de HTML, tokenização, remoção de stopwords e stemming."""
    try:
        # 1. Limpeza: Remoção de tags de script/style e extração de texto
        soup = BeautifulSoup(conteudo_html, 'html.parser')
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        texto_limpo = soup.get_text(separator=' ')
    except Exception as e:
        logger.error(f"Erro na BeautifulSoup ao processar HTML. {e}")
        texto_limpo = ""

    # 2. Normalização e Tokenização
    limpo = re.sub(r'[^a-zA-ZáéíóúàèìòùãõâêîôûçÁÉÍÓÚÀÈÌÒÙÃÕÂÊÎÔÛÇ\s]', '', texto_limpo).lower()
    tokens = limpo.split()

    # 3. Filtra stopwords, aplica stemming
    return [STEMMER.stem(token) for token in tokens if token not in STOPWORDS and len(token) > 2]