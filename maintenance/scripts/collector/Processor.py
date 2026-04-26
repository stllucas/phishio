"""Corpo lógico e orquestrador do processo de coleta web."""
import datetime
import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from tqdm import tqdm

from runtime.core.Config import (
    BASE_PATH,
    DATASETS_DIR,
    LOG_DIR_OUTPUT,
    OUTPUT_DIR_TEMP,
    ZIP_OUTPUT_DIR,
)
from runtime.core.Logging import setup_logging
from .Relatorio import GeradorRelatorio
from .Verificador import Verificador

logger = setup_logging()

URL_COLUMN_NAME = 'URL'

LOG_FILE = os.path.join(LOG_DIR_OUTPUT, 'collection_log.csv')
ERROR_LOG_FILE = os.path.join(LOG_DIR_OUTPUT, 'error_log.txt')

URL_FILES = [
    os.path.join(DATASETS_DIR, 'taruntiwarihp_dataset.csv'),
    os.path.join(DATASETS_DIR, 'mendeley_dataset.csv')
]

MAX_WORKERS = 15
TIMEOUT_SECONDS = 30

os.makedirs(OUTPUT_DIR_TEMP, exist_ok=True)
os.makedirs(ZIP_OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR_OUTPUT, exist_ok=True)

logger.info(f"Pasta de trabalho temporária pronta em: '{OUTPUT_DIR_TEMP}'")
logger.info(f"Arquivos .zip serão salvos em: '{ZIP_OUTPUT_DIR}'")
logger.info(f"Logs de resultados (CSV) serão salvos em: '{LOG_DIR_OUTPUT}'")


def finalize_collection():
    logger.info("\n" + "="*50)
    logger.info("INICIANDO PROCESSO DE FINALIZAÇÃO...")
    logger.info("="*50)

    if not os.path.isdir(OUTPUT_DIR_TEMP) or not os.listdir(OUTPUT_DIR_TEMP):
        logger.warning(
            "Nenhum arquivo novo foi baixado nesta sessão. Nenhum arquivo .zip será criado.")
        return

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename_base = f'coleta_html_{timestamp}'
    zip_path_final = os.path.join(ZIP_OUTPUT_DIR, zip_filename_base)

    logger.info(f"Compactando arquivos para: {zip_path_final}.zip")

    try:
        shutil.make_archive(zip_path_final, 'zip', OUTPUT_DIR_TEMP)
        logger.info("\nSucesso!")
        logger.info(f"Arquivo compactado salvo em: {zip_path_final}.zip")
    except Exception as e:
        logger.error(f"Ocorreu um erro ao compactar os arquivos: {e}")


def main():
    logger.info("="*50)
    logger.info("INICIANDO PROCESSO DE COLETA DE PÁGINAS HTML")
    logger.info("="*50)

    Verificador.set_config(OUTPUT_DIR_TEMP, TIMEOUT_SECONDS)

    completed_urls = set()
    try:
        if os.path.exists(LOG_FILE):
            log_df = pd.read_csv(LOG_FILE, on_bad_lines='skip')
            if not log_df.empty and 'status' in log_df.columns and 'original_url' in log_df.columns:
                success_df = log_df[log_df['status'].str.startswith(
                    'SUCCESS', na=False)]
                completed_urls = set(success_df['original_url'])
                logger.info(
                    f"Log de execuções anteriores encontrado. {len(completed_urls)} URLs já coletadas com sucesso.")
    except Exception as e:
        logger.warning(
            f"Falha ao ler o log de URLs concluídas: {e}. A coleta pode reprocessar algumas URLs.")

    all_dfs = []

    try:
        df_generator = (pd.read_csv(f, engine='python',
                        on_bad_lines='skip') for f in URL_FILES)
        all_dfs = [df for df in df_generator]
        df = pd.concat(all_dfs, ignore_index=True)
        initial_count = len(df)
        df.drop_duplicates(subset=[URL_COLUMN_NAME],
                           keep='first', inplace=True)

        duplicates_removed = initial_count - len(df)
        if duplicates_removed > 0:
            logger.info(
                f"Desduplicação de URLs concluída: {duplicates_removed} URLs duplicadas foram removidas.")

    except Exception as e:
        logger.error(
            f"Erro CRÍTICO ao ler e concatenar os arquivos de URLs: {e}")
        return False, []

    raw_urls = df[URL_COLUMN_NAME].dropna().unique().tolist()
    urls = []
    for u in raw_urls:
        if isinstance(u, str):
            if not u.startswith(('http://', 'https://')):
                urls.append(f'http://{u}')
            else:
                urls.append(u)

    total_urls = len(urls)
    urls_to_collect = [url for url in urls if url not in completed_urls]
    print_summary(total_urls, len(completed_urls), len(urls_to_collect))

    if not urls_to_collect:
        logger.info("Nenhuma URL nova para coletar. A tarefa já foi concluída!")
        return True, []

    needs_header = not os.path.exists(LOG_FILE)

    with open(LOG_FILE, 'a', encoding='utf-8', newline='') as log_f:
        if needs_header:
            log_f.write("original_url,saved_filename,status\n")

        with tqdm(total=len(urls_to_collect), desc="Coletando Páginas Restantes") as pbar:
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                chunk_size = 10000
                for i in range(0, len(urls_to_collect), chunk_size):
                    chunk = urls_to_collect[i:i + chunk_size]
                    future_to_url = {executor.submit(
                        Verificador.download_url, url): url for url in chunk}
                    for future in as_completed(future_to_url):
                        try:
                            original_url, saved_filename, status = future.result()
                            log_f.write(
                                f'"{original_url}","{saved_filename}","{status}"\n')
                        except Exception as exc:
                            url_falha = future_to_url[future]
                            logger.critical(
                                f"FATAL_ERROR no Executor para {url_falha}: {exc}")
                            log_f.write(
                                f'"{url_falha}","","FATAL_ERROR_during_future_result_{exc}"\n')
                        pbar.update(1)

    logger.info("\nCOLETA DE PÁGINAS FINALIZADA!")
    return True, urls_to_collect


def print_summary(total, completed, remaining):
    logger.info("-" * 50)
    logger.info("Resumo da Tarefa:")
    logger.info(f"Total de URLs na fonte: {total}")
    logger.info(f"URLs já completas (de execuções anteriores): {completed}")
    logger.info(f"URLs a serem processadas nesta sessão: {remaining}")
    logger.info("-" * 50)


def run_post_processing(collection_successful, attempted_urls):
    """Executa a geração de relatórios e a finalização após a coleta."""

    if collection_successful:

        logger.info("\n" + "="*50)
        logger.info("GERANDO RELATÓRIOS CONSOLIDADOS (SUCESSO/ERRO)")
        logger.info("="*50)

        relatorio_status = GeradorRelatorio.gerar_relatorios_consolidados(
            LOG_FILE, BASE_PATH)

        if relatorio_status["success_path"]:
            logger.info(
                f"Relatório de Sucesso (Total: {relatorio_status['success_count']}) salvo em: {relatorio_status['success_path']}")
        if relatorio_status["error_path"]:
            logger.info(
                f"Relatório de Erros (Total: {relatorio_status['error_count']}) salvo em: {relatorio_status['error_path']}")

        if attempted_urls:
            try:
                log_df = pd.read_csv(LOG_FILE, on_bad_lines='skip')
                session_df = log_df[log_df['original_url'].isin(
                    attempted_urls)]
                error_urls = session_df[session_df['status'].str.startswith(
                    ('ERROR', 'FATAL_ERROR'), na=False)]['original_url']

                if not error_urls.empty:
                    with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
                        for url in error_urls:
                            f.write(f"{url}\n")
                    logger.info(
                        f"📄 Uma lista com as {len(error_urls)} URLs que falharam *nesta sessão* foi salva em: '{ERROR_LOG_FILE}'")
            except Exception as e:
                logger.error(f"Falha ao gerar o log de erros da sessão: {e}")

        finalize_collection()
