from pathlib import Path

# BASE_PATH é a raiz do projeto ('phishio'), calculada subindo 3 níveis.
# Esta lógica continua funcionando mesmo com a nova estrutura.
BASE_PATH = Path(__file__).resolve().parent.parent.parent

# --- Diretórios Principais ---
DATA_DIR = BASE_PATH / 'data'
LOG_FILES_DIR = BASE_PATH / 'logs'  # Para logs de execução (.log)

# --- Subdiretórios de 'data' ---
# Para datasets de entrada (CSVs)
DATASETS_DIR = DATA_DIR / 'datasets'

# Para dados brutos coletados
RAW_DATA_DIR = DATA_DIR / 'raw'
HTML_PAGES_TEMP_DIR = RAW_DATA_DIR / 'html_pages_temp'

# Para dados processados e artefatos gerados
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
ZIPPED_COLLECTIONS_DIR = PROCESSED_DATA_DIR / 'collections'
# Para indice_invertido.json, etc.
INDEX_ARTIFACTS_DIR = PROCESSED_DATA_DIR / 'index'

# --- Arquivos de Configuração e Credenciais ---
SECRETS_FILE = BASE_PATH / 'secrets'

# --- ALIASES PARA COMPATIBILIDADE com código legado ---
# O código antigo usava LOG_DIR para salvar artefatos.
# Mantemos o alias apontando para o novo local de artefatos para minimizar quebras.
LOG_DIR = INDEX_ARTIFACTS_DIR
LOG_DIR_OUTPUT = INDEX_ARTIFACTS_DIR
OUTPUT_DIR_TEMP = HTML_PAGES_TEMP_DIR
ZIP_OUTPUT_DIR = ZIPPED_COLLECTIONS_DIR


def get_index_artifact_path(filename: str) -> Path:
    """Retorna o caminho completo para um artefato de índice (json, bin, etc.)."""
    return INDEX_ARTIFACTS_DIR / filename
