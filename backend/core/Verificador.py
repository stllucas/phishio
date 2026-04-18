# ==============================================================================
# verificador.py (Logs de Status em Tempo Real)
# ==============================================================================
import hashlib
import logging
import os

import requests

# Obtém o logger configurado (garante que ColetorLogger esteja em log_config.py)
logger = logging.getLogger('ColetorLogger')


class Verificador:
    """
    Realiza o download de uma URL e salva o conteúdo em um arquivo.
    """

    OUTPUT_DIR_TEMP = None
    TIMEOUT_SECONDS = 15

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    @classmethod
    def format_error_message(cls, exception_message):
        """Formata uma mensagem de exceção para ser segura em CSV e curta."""
        msg = str(exception_message).split('\n')[0]
        return msg.replace(',', ';').replace('"', "'")

    @classmethod
    def set_config(cls, output_dir_temp, timeout_seconds):
        """Define as configurações necessárias para a classe."""
        cls.OUTPUT_DIR_TEMP = output_dir_temp
        cls.TIMEOUT_SECONDS = timeout_seconds

    @classmethod
    def download_url(cls, url):
        """
        Tenta baixar a URL e salva no diretório temporário.
        """
        if not cls.OUTPUT_DIR_TEMP:
            logger.critical(
                "ERRO CRÍTICO DE CONFIGURAÇÃO: OUTPUT_DIR_TEMP não configurado.")
            raise RuntimeError(
                "OUTPUT_DIR_TEMP não configurado. Chame Verificador.set_config() primeiro.")

        filename = hashlib.md5(url.encode('utf-8')).hexdigest() + '.html'
        filepath = os.path.join(cls.OUTPUT_DIR_TEMP, filename)
        response = None  # Inicializa response

        try:
            response = requests.get(
                url,
                headers=cls.HEADERS,
                timeout=cls.TIMEOUT_SECONDS,
                allow_redirects=True
            )
            response.raise_for_status()  # Lança exceção para 4xx e 5xx

            logger.info(f"SUCCESS: {url} -> Status {response.status_code}")

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)

            return (url, filename, f'SUCCESS_{response.status_code}')

        except requests.exceptions.RequestException as e:
            error_message = cls.format_error_message(e)
            status_code = response.status_code if response is not None else "N/A"

            if response is not None and status_code >= 400:
                logger.error(
                    f"HTTP_ERROR: Status {status_code} ({error_message}) -> URL: {url}")
            else:
                logger.error(
                    f"NETWORK_FAILURE: Status {status_code} ({error_message}) -> URL: {url}")

            return (url, filename, f'ERROR_{error_message}')

        except Exception as e:
            error_message = cls.format_error_message(e)
            logger.critical(
                f"FATAL_ERROR: {url} -> Falha Interna ({error_message})")
            return (url, filename, f'FATAL_ERROR_{error_message}')
