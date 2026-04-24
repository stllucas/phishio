"""Configuração do sistema de logging do coletor."""
import logging
import os
from datetime import datetime

from .Config import LOG_FILES_DIR

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

    log_execution_dir = os.path.join(LOG_FILES_DIR, 'execution_log')
    os.makedirs(log_execution_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(
        log_execution_dir, f'coletor_run_{timestamp}.log')
    _LOG_FILENAME = log_filename

    logger = logging.getLogger('ColetorLogger')
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

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
