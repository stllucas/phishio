"""Script auxiliar para diagnóstico e Health Check do estado do sistema de RI."""
import json
import sys
from os.path import abspath, dirname

import pandas as pd

BACKEND_DIR = dirname(dirname(abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


try:
    from runtime.core.Config import get_index_artifact_path
    from runtime.core.Logging import setup_logging
    logger = setup_logging()
except ImportError:
    class FallbackLogger:
        def info(self, msg): print(msg)
        def warning(self, msg): print(f"AVISO: {msg}")
        def error(self, msg): print(f"ERRO: {msg}")
    logger = FallbackLogger()


def verificar_integridade_sistema():
    """
    Executa uma verificação completa (Health Check) do estado do sistema,
    analisando os artefatos da coleta, indexação e cálculo de IDF.
    """
    logger.info("-" * 50)
    logger.info("INICIANDO VERIFICAÇÃO DE INTEGRIDADE DO SISTEMA DE RI")
    logger.info("-" * 50)

    caminho_arquivo_log = get_index_artifact_path('collection_log.csv')
    logger.info(f"1. Verificando log de coleta: {caminho_arquivo_log}")

    if not caminho_arquivo_log.exists():
        logger.warning(
            "Arquivo de log da coleta (collection_log.csv) não encontrado. Pule para a próxima verificação.")
    else:
        try:
            df_log = pd.read_csv(caminho_arquivo_log,
                                 on_bad_lines='skip', low_memory=False)
            total_entradas = len(df_log)
            df_sucesso = df_log[df_log['status'].str.startswith(
                'SUCCESS', na=False)]
            total_coletado_unico = df_sucesso['original_url'].nunique()

            logger.info(
                f"   - Total de tentativas de coleta registradas: {total_entradas}")
            logger.info(
                f"   - URLs únicas coletadas com sucesso: {total_coletado_unico}")
        except Exception as e:
            logger.error(
                f"   - ERRO CRÍTICO ao processar o log de coleta: {e}")

    artefatos = {
        "Mapa de Documentos": "document_map.json",
        "Índice Invertido": "indice_invertido.json",
        "Pesos IDF": "idf.json"
    }

    for nome_artefato, nome_arquivo in artefatos.items():
        logger.info(
            f"\n2.{list(artefatos.keys()).index(nome_artefato) + 1}. Verificando Artefato: {nome_artefato}")
        caminho_arquivo = get_index_artifact_path(nome_arquivo)
        if not caminho_arquivo.exists():
            logger.warning(f"   - ARQUIVO NÃO ENCONTRADO: {caminho_arquivo}")
            logger.warning(
                "   - Execute a etapa correspondente para gerá-lo (Indexação ou Cálculo de IDF).")
            continue

        try:
            tamanho_bytes = caminho_arquivo.stat().st_size
            tamanho_mb = tamanho_bytes / (1024 * 1024)
            logger.info(f"   - Arquivo encontrado: {caminho_arquivo}")
            logger.info(f"   - Tamanho: {tamanho_mb:.2f} MB")

            if nome_arquivo in ["document_map.json", "idf.json"]:
                with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    numero_entradas = len(dados)
                    if nome_arquivo == "document_map.json":
                        logger.info(
                            f"   - Total de documentos mapeados: {numero_entradas}")
                    else:
                        logger.info(
                            f"   - Total de termos no vocabulário (com IDF): {numero_entradas}")

            elif nome_arquivo == "indice_invertido.json":
                try:
                    import ijson
                    logger.info(
                        "   - Analisando o número de termos (pode levar um tempo)...")
                    numero_termos = 0
                    with open(caminho_arquivo, 'rb') as f:
                        for _ in ijson.kvitems(f, ''):
                            numero_termos += 1
                    logger.info(
                        f"   - Total de termos únicos no vocabulário: {numero_termos}")
                except ImportError:
                    logger.warning(
                        "   - A biblioteca 'ijson' não está instalada. Não é possível contar os termos.")
                    logger.warning("   - Instale com: pip install ijson")
                except Exception as e:
                    logger.error(
                        f"   - ERRO ao analisar o índice com ijson: {e}")

        except json.JSONDecodeError:
            logger.error(
                f"   - ERRO: O arquivo '{nome_arquivo}' está corrompido (não é um JSON válido).")
        except Exception as e:
            logger.error(
                f"   - ERRO ao analisar o arquivo '{nome_arquivo}': {e}")

    logger.info("-" * 50)
    logger.info("VERIFICAÇÃO DE INTEGRIDADE FINALIZADA")
    logger.info("-" * 50)


if __name__ == '__main__':
    verificar_integridade_sistema()
