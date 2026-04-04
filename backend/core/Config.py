import os

# Caminho absoluto da raiz do projeto (um nível acima de src/)
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Pastas padrão (na raiz do projeto)
LOG_DIR = os.path.join(BASE_PATH, 'logs')
# Alias usado por arquivos existentes
LOG_DIR_OUTPUT = LOG_DIR

# Pasta temporária para salvar páginas HTML coletadas
OUTPUT_DIR_TEMP = os.path.join(BASE_PATH, 'html_pages_temp')

# Pasta para armazenar as coletas compactadas (.zip)
ZIP_OUTPUT_DIR = os.path.join(BASE_PATH, 'coletas_compactadas')

def get_log_file_path(filename):
    """Retorna o caminho completo para um arquivo dentro da pasta de logs."""
    return os.path.join(LOG_DIR, filename)
