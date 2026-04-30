"""Configurações globais e mapeamento de diretórios do projeto."""
from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_PATH / 'data'
RUNTIME_DIR = BASE_PATH / 'runtime'

DOCUMENT_MAP_PATH = DATA_DIR / 'document_map.json'
POSTINGS_BIN_PATH = DATA_DIR / 'postings.bin'
VOCAB_PATH        = DATA_DIR / 'vocabulario.json'
IDF_PATH          = DATA_DIR / 'idf.json'
NORMS_PATH        = DATA_DIR / 'norms.json'

SECRETS_FILE = RUNTIME_DIR / 'secrets'

INDEX_ARTIFACTS_DIR = DATA_DIR
LOG_DIR_OUTPUT = DATA_DIR
