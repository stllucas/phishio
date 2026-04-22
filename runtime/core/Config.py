from pathlib import Path

# Raiz do projeto: /var/www/phishio
BASE_PATH = Path(__file__).resolve().parent.parent.parent

# --- Diretórios ---
DATA_DIR = BASE_PATH / 'data'
RUNTIME_DIR = BASE_PATH / 'runtime'

# --- Artefatos de Índice (Caminho Achatado na Camada WARM) ---
DOCUMENT_MAP_PATH = DATA_DIR / 'document_map.json'
POSTINGS_BIN_PATH = DATA_DIR / 'postings.bin'
VOCAB_PATH        = DATA_DIR / 'vocabulario.json'
IDF_PATH          = DATA_DIR / 'idf.json'
NORMS_PATH        = DATA_DIR / 'norms.json'

# --- Credenciais ---
SECRETS_FILE = RUNTIME_DIR / 'secrets'

# Aliases para compatibilidade legada
INDEX_ARTIFACTS_DIR = DATA_DIR
LOG_DIR_OUTPUT = DATA_DIR
