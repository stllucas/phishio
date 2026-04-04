# ==============================================================================
# d:\lucas\Documents\TCC\phishio\scripts\data_prep\linguistic.py
# Módulo centralizado para processamento de texto (tokenização, stemming, etc.)
# ==============================================================================
import re
try:
    from nltk.corpus import stopwords
    from nltk.stem.snowball import SnowballStemmer
except ImportError:
    raise ImportError("NLTK não encontrado. Por favor, execute o setup.bat ou instale com 'pip install nltk'.")

STOPWORDS = set(stopwords.words('portuguese'))
STEMMER = SnowballStemmer('portuguese')

def process_text(text: str) -> list[str]:
    """
    Aplica o pipeline de limpeza e processamento linguístico a um texto.
    1. Remove caracteres não alfabéticos e converte para minúsculas.
    2. Tokeniza o texto.
    3. Remove stopwords e tokens curtos.
    4. Aplica stemming.
    """
    limpo = re.sub(r'[^a-zA-ZáéíóúàèìòùãõâêîôûçÁÉÍÓÚÀÈÌÒÙÃÕÂÊÎÔÛÇ\s]', '', text).lower()
    tokens = limpo.split()
    tokens_processados = [STEMMER.stem(token) for token in tokens if token not in STOPWORDS and len(token) > 2]
    return tokens_processados
