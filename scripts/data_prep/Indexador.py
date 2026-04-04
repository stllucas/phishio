# ==============================================================================
# src/Indexador.py
# Módulo responsável pela Representação e Indexação dos dados coletados.
# ==============================================================================
import os
import json
import pandas as pd
from collections import defaultdict
from logging import getLogger
from .linguistic import process_text

# Configuração do Logger
logger = getLogger('ColetorLogger')

class Indexador:
    """
    Constrói e salva o Índice Invertido a partir dos arquivos HTML coletados.
    """

    @classmethod
    def construir_indice_invertido(cls, caminho_arquivo_log, diretorio_html):
        """
        Lê o log de sucesso e os arquivos HTML DISPONÍVEIS para construir o índice invertido.
        """
        
        logger.info("Iniciando construção do Índice Invertido...")
        
        indice_invertido = defaultdict(lambda: {'df': 0, 'postings': {}})
        mapa_documentos = {} # {id_documento: url_original}
        
        try:
            # --- Leitura  do CSV ---
            # Especifica o motor 'python' e o 'quotechar' para lidar corretamente
            # com mensagens de erro que contêm caracteres especiais dentro das colunas.
            log_df = pd.read_csv(
                caminho_arquivo_log, on_bad_lines='skip', low_memory=False, engine='python', quotechar='"'
            )
            
            # --- VERIFICAÇÃO: Executada ANTES de acessar as colunas ---
            colunas_necessarias = {'status', 'saved_filename', 'original_url'}
            if log_df.empty or not colunas_necessarias.issubset(log_df.columns):
                msg_erro = ("O arquivo de log ('collection_log.csv') está vazio ou malformado. "
                            "Execute a Etapa 1 (Coleta) primeiro para gerar um log válido.")
                logger.error(msg_erro)
                return None, None, msg_erro
            df_sucesso = log_df[log_df['status'].str.startswith('SUCCESS')]
            
            # --- 1. OTIMIZAÇÃO CRÍTICA: Filtra apenas arquivos disponíveis em disco ---
            # Isso impede que o Indexador tente abrir arquivos que o antivírus deletou.
            arquivos_disponiveis = set(os.listdir(diretorio_html))
            df_para_indexar = df_sucesso[df_sucesso['saved_filename'].isin(arquivos_disponiveis)]
            
            total_documentos_log = len(df_sucesso)
            total_documentos_para_indexar = len(df_para_indexar)
            total_docs_faltando = total_documentos_log - total_documentos_para_indexar
            
            logger.info(f"Total de documentos no log (Histórico): {total_documentos_log}")
            logger.info(f"Total de documentos encontrados e prontos para indexação: {total_documentos_para_indexar}")
            logger.warning(f"Total de documentos FALTANTES (deletados/limpos): {total_docs_faltando}")
            
            if total_documentos_para_indexar == 0:
                msg_erro = "Nenhum arquivo HTML para indexar foi encontrado na pasta temporária. Execute a Etapa 1 (Coleta)."
                logger.error(msg_erro)
                return None, None, msg_erro
                
            # Itera apenas sobre os documentos que realmente existem
            for id_documento, linha in enumerate(df_para_indexar.itertuples()):
                caminho_arquivo = os.path.join(diretorio_html, linha.saved_filename)
                
                # --- 2. TRATAMENTO DE ERRO AO ABRIR ---
                try:
                    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                except OSError as e:
                    # Captura erros de I/O de última hora (improvável com o filtro, mas seguro)
                    logger.error(f"ERRO DE ARQUIVO CRÍTICO (Ignorado): Falha I/O ao ler {linha.saved_filename}. Erro: {e}")
                    continue 

                # Utiliza o novo módulo de processamento de texto
                termos_processados = process_text(conteudo)
                mapa_documentos[id_documento] = linha.original_url
                
                # Frequência de Termos (TF) para o documento atual
                termo_frequencia = defaultdict(int)
                for termo in termos_processados:
                    termo_frequencia[termo] += 1
                
                # Atualizar o índice invertido
                for termo, tf in termo_frequencia.items():
                    # df (Document Frequency): Contagem de documentos que contêm o termo
                    if id_documento not in indice_invertido[termo]['postings']:
                         indice_invertido[termo]['df'] += 1
                         
                    # postings: Armazenamos a Frequência do Termo (TF) para o doc_id
                    indice_invertido[termo]['postings'][id_documento] = tf 
            
            logger.info(f"Índice construído. Total de termos únicos: {len(indice_invertido)}")
            return indice_invertido, mapa_documentos, None # Retorna None para o erro em caso de sucesso
        
        except Exception as e:
            # Captura falhas na leitura do CSV ou erros de DataFrame
            msg_erro = f"Falha CRÍTICA na construção do índice. Erro: {e}"
            logger.critical(msg_erro)
            return None, None, msg_erro
            
    @staticmethod
    def salvar_indice(indice, mapa_documentos, diretorio_saida):
        """Salva o índice e o mapa de documentos em formato JSON na pasta de saída."""
        
        caminho_saida_indice = os.path.join(diretorio_saida, 'indice_invertido.json')
        caminho_saida_mapa = os.path.join(diretorio_saida, 'document_map.json')
        
        # 1. Salva o Índice Invertido
        with open(caminho_saida_indice, 'w', encoding='utf-8') as f:
            json.dump(dict(indice), f, ensure_ascii=False, indent=2)
        
        # 2. Salva o Mapa de Documentos
        with open(caminho_saida_mapa, 'w', encoding='utf-8') as f:
            json.dump(mapa_documentos, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Arquivos do Índice salvos com sucesso em: {diretorio_saida}")