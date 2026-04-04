# ==============================================================================
# log_config.py (VERSÃO FINAL: Logs com Timestamp e Pasta)
# ==============================================================================
import logging
import os
from datetime import datetime

# Cache do logger para tornar a configuração idempotente
_LOGGER = None
_LOG_FILENAME = None

def setup_logging():
    """
    Configura o sistema de logging do coletor.

    Esta função é idempotente: múltiplas chamadas retornam o mesmo logger
    e não reaplicam handlers nem reimprimem a mensagem de criação do
    arquivo de log.
    """
    global _LOGGER, _LOG_FILENAME
    if _LOGGER is not None:
        return _LOGGER

    # 1. Definir o subdiretório para logs de execução
    from Config import LOG_DIR
    log_execution_dir = os.path.join(LOG_DIR, 'execution_log')
    os.makedirs(log_execution_dir, exist_ok=True)

    # 2. Gerar o nome do arquivo com timestamp dentro do novo diretório
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_execution_dir, f'coletor_run_{timestamp}.log')
    _LOG_FILENAME = log_filename

    # 3. Configuração do Logger
    logger = logging.getLogger('ColetorLogger')
    logger.setLevel(logging.INFO)  # Nível mínimo para logging

    # Formato do log
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Handler para o arquivo (novo log a cada execução)
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(formatter)

    # Handler para o console (acompanhamento em tempo real)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # Limpar handlers antigos, se houver (garante configuração limpa)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Adicionar handlers
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # Notificar o usuário sobre o novo arquivo de log (apenas na primeira vez)
    logger.info(f"O log desta execução está sendo salvo em: {log_filename}")

    _LOGGER = logger
    return _LOGGER


def get_logger():
    """Retorna o logger já configurado (configura se necessário)."""
    return setup_logging()


def get_log_file():
    """Retorna o path do arquivo de log da execução atual."""
    if _LOG_FILENAME is None:
        setup_logging()
    return _LOG_FILENAME