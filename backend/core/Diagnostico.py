# ==============================================================================
# Script auxiliar para diagnóstico (Health Check) do sistema.
# ==============================================================================
import os
import sys
import json
import pandas as pd
from Config import LOG_DIR_OUTPUT, get_log_file_path

# 1. Configurar o Python Path (CRUCIAL se estiver na raiz)
# Se este arquivo estiver na RAIZ, precisamos configurar o caminho para 'src'
RAIZ_PROJETO = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_SRC = os.path.join(RAIZ_PROJETO, 'src')
if DIRETORIO_SRC not in sys.path:
    sys.path.append(DIRETORIO_SRC)

# 2. Importar o logger (opcional, mas recomendado para formatar a saída)
try:
    from Logging import setup_logging, get_log_file
    # Inicializa o logger para esta execução
    logger = setup_logging()
except ImportError:
    # Fallback se o logging falhar (para que o script ainda funcione)
    def logger_info(msg):
        print(msg)
    logger = type('Logger', (object,), {'info': logger_info})()


def verificar_integridade_sistema():
    """
    Executa uma verificação completa (Health Check) do estado do sistema,
    analisando os artefatos da coleta, indexação e cálculo de IDF.
    """
    logger.info("-" * 50)
    logger.info("INICIANDO VERIFICAÇÃO DE INTEGRIDADE DO SISTEMA DE RI")
    logger.info("-" * 50)

    # --- 1. Verificação da Coleta (collection_log.csv) ---
    caminho_arquivo_log = get_log_file_path('collection_log.csv')
    logger.info(f"1. Verificando log de coleta: {caminho_arquivo_log}")
    
    if not os.path.exists(caminho_arquivo_log):
        logger.warning("Arquivo de log da coleta (collection_log.csv) não encontrado. Pule para a próxima verificação.")
    else:
        try:
            df_log = pd.read_csv(caminho_arquivo_log, on_bad_lines='skip', low_memory=False)
            total_entradas = len(df_log)
            df_sucesso = df_log[df_log['status'].str.startswith('SUCCESS', na=False)]
            total_coletado_unico = df_sucesso['original_url'].nunique()
            
            logger.info(f"   - Total de tentativas de coleta registradas: {total_entradas}")
            logger.info(f"   - URLs únicas coletadas com sucesso: {total_coletado_unico}")
        except Exception as e:
            logger.error(f"   - ERRO CRÍTICO ao processar o log de coleta: {e}")

    # --- 2. Verificação dos Artefatos de Indexação e IDF ---
    artefatos = {
        "Mapa de Documentos": "document_map.json",
        "Índice Invertido": "indice_invertido.json",
        "Pesos IDF": "idf.json"
    }

    for nome_artefato, nome_arquivo in artefatos.items():
        logger.info(f"\n2.{list(artefatos.keys()).index(nome_artefato) + 1}. Verificando Artefato: {nome_artefato}")
        caminho_arquivo = get_log_file_path(nome_arquivo)
        if not os.path.exists(caminho_arquivo):
            logger.warning(f"   - ARQUIVO NÃO ENCONTRADO: {caminho_arquivo}")
            logger.warning(f"   - Execute a etapa correspondente para gerá-lo (Indexação ou Cálculo de IDF).")
            continue

        try:
            tamanho_bytes = os.path.getsize(caminho_arquivo)
            tamanho_mb = tamanho_bytes / (1024 * 1024)
            logger.info(f"   - Arquivo encontrado: {caminho_arquivo}")
            logger.info(f"   - Tamanho: {tamanho_mb:.2f} MB")

            # Adiciona estatísticas específicas para cada arquivo
            if nome_arquivo in ["document_map.json", "idf.json"]:
                with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    numero_entradas = len(dados)
                    if nome_arquivo == "document_map.json":
                        logger.info(f"   - Total de documentos mapeados: {numero_entradas}")
                    else: # idf.json
                        logger.info(f"   - Total de termos no vocabulário (com IDF): {numero_entradas}")

            # --- Verificação específica para o Índice Invertido (usando ijson para arquivos grandes) ---
            elif nome_arquivo == "indice_invertido.json":
                try:
                    import ijson
                    logger.info("   - Analisando o número de termos (pode levar um tempo)...")
                    numero_termos = 0
                    with open(caminho_arquivo, 'rb') as f: # ijson prefere modo binário
                        # Itera sobre as chaves do objeto raiz sem carregar os valores
                        for _ in ijson.kvitems(f, ''):
                            numero_termos += 1
                    logger.info(f"   - Total de termos únicos no vocabulário: {numero_termos}")
                except ImportError:
                    logger.warning("   - A biblioteca 'ijson' não está instalada. Não é possível contar os termos.")
                    logger.warning("   - Instale com: pip install ijson")
                except Exception as e:
                    logger.error(f"   - ERRO ao analisar o índice com ijson: {e}")

        except json.JSONDecodeError:
            logger.error(f"   - ERRO: O arquivo '{nome_arquivo}' está corrompido (não é um JSON válido).")
        except Exception as e:
            logger.error(f"   - ERRO ao analisar o arquivo '{nome_arquivo}': {e}")

    logger.info("-" * 50)
    logger.info("VERIFICAÇÃO DE INTEGRIDADE FINALIZADA")
    logger.info("-" * 50)

if __name__ == '__main__':
    verificar_integridade_sistema()