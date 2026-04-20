from pathlib import Path

# BASE_PATH é a raiz do projeto ('phishio'), calculada subindo 3 níveis a partir de 'runtime/core'.
BASE_PATH = Path(__file__).resolve().parent.parent.parent

# --- Diretórios Principais ---
# A nova estrutura centraliza todos os dados de artefatos em 'data/'.
DATA_DIR = BASE_PATH / 'data'
LOG_FILES_DIR = BASE_PATH / 'logs'
# O diretório de artefatos do índice (postings, vocabulário, etc.) agora aponta diretamente para 'data/'.
INDEX_ARTIFACTS_DIR = DATA_DIR

# --- Arquivos de Configuração e Credenciais ---
# O arquivo de segredos agora reside dentro da pasta 'runtime'.
SECRETS_FILE = BASE_PATH / 'runtime' / 'secrets'

# --- ALIASES PARA COMPATIBILIDADE com código legado ---
# O código antigo usava LOG_DIR para salvar artefatos.
# Mantemos o alias apontando para o novo local de artefatos para minimizar quebras.
LOG_DIR = INDEX_ARTIFACTS_DIR
LOG_DIR_OUTPUT = INDEX_ARTIFACTS_DIR


def get_index_artifact_path(filename: str) -> Path:
    """Retorna o caminho completo para um artefato de índice (json, bin, etc.)."""
    return INDEX_ARTIFACTS_DIR / filename
