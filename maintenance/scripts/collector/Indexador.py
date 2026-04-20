# ==============================================================================
# src/Indexador.py
# Módulo responsável pela Representação e Indexação dos dados coletados.
# ==============================================================================
import json
import os
import re
import warnings
from collections import defaultdict
from logging import getLogger

import nltk
import pandas as pd
from bs4 import BeautifulSoup

# Configuração do Logger
logger = getLogger('ColetorLogger')

# Baixa os recursos do NLTK se necessário
try:
    # 'quiet=True' evita poluição do log se já estiverem baixados
    nltk.download('stopwords', quiet=True)
    # Tenta baixar o 'punkt' para tokenização mais avançada, se necessário
    # Embora usemos split(), é bom para a compatibilidade futura
    nltk.download('punkt', quiet=True)
except Exception:
    warnings.warn(
        "NLTK stopwords ou punkt não baixados. Verifique a instalação.", UserWarning)


# Define recursos de Processamento de Linguagem Natural (PLN)
# -----------------------------------------------------------
try:
    STOPWORDS = set(nltk.corpus.stopwords.words('portuguese'))
    STEMMER = nltk.stem.SnowballStemmer("portuguese")
except LookupError:
    # Fallback seguro caso os recursos do NLTK não estejam disponíveis
    logger.error(
        "Recursos do NLTK para português não carregados. Stemming e Stopwords estão DESATIVADOS.")
    STOPWORDS = set()

    def STEMMER(x):
        return x


class Indexador:
    """
    Constrói e salva o Índice Invertido a partir dos arquivos HTML coletados.
    """

    @staticmethod
    def _remover_tags_e_obter_texto(conteudo_html):
        """Usa BeautifulSoup para remover tags de estrutura (scripts/styles) e obter o texto visível."""
        try:
            soup = BeautifulSoup(conteudo_html, 'html.parser')

            # Remove elementos de estilo e script, que não são conteúdo de busca
            for script_or_style in soup(['script', 'style']):
                script_or_style.decompose()

            # Retorna o texto visível, usando espaço como separador
            return soup.get_text(separator=' ')
        except Exception as e:
            logger.error(f"Erro na BeautifulSoup ao processar HTML. {e}")
            return ""

    @classmethod
    def limpar_e_tokenizar(cls, conteudo_html):
        """Aplica análise léxica: limpeza, tokenização, remoção de stopwords e stemming."""

        # 1. Limpeza: Remoção de tags
        texto_limpo = cls._remover_tags_e_obter_texto(conteudo_html)

        # 2. Normalização: Padronização para minúsculas e remoção de caracteres
        # Mantém letras e acentos do português; remove pontuação e números
        limpo = re.sub(
            r'[^a-zA-ZáéíóúàèìòùãõâêîôûçÁÉÍÓÚÀÈÌÒÙÃÕÂÊÎÔÛÇ\s]', '', texto_limpo).lower()

        # 3. Tokenização por espaço
        tokens = limpo.split()

        tokens_processados = []
        for token in tokens:
            # 4. Filtra stopwords e tokens muito curtos
            if token not in STOPWORDS and len(token) > 2:
                # 5. Stemming
                tokens_processados.append(STEMMER.stem(token))

        return tokens_processados

    @classmethod
    def construir_indice_invertido(cls, log_file_path, html_dir):
        """
        Lê o log de sucesso e os arquivos HTML DISPONÍVEIS para construir o índice invertido.
        """

        logger.info("Iniciando construção do Índice Invertido...")

        indice_invertido = defaultdict(lambda: {'df': 0, 'postings': {}})
        document_map = {}  # {doc_id: original_url}

        try:
            # --- Leitura  do CSV ---
            # Especifica o motor 'python' e o 'quotechar' para lidar corretamente
            # com mensagens de erro que contêm caracteres especiais dentro das colunas.
            log_df = pd.read_csv(
                log_file_path, on_bad_lines='skip', low_memory=False, engine='python', quotechar='"'
            )

            # --- VERIFICAÇÃO: Executada ANTES de acessar as colunas ---
            colunas_necessarias = {'status', 'saved_filename', 'original_url'}
            if log_df.empty or not colunas_necessarias.issubset(log_df.columns):
                msg_erro = ("O arquivo de log ('collection_log.csv') está vazio ou malformado. "
                            "Execute a Etapa 1 (Coleta) primeiro para gerar um log válido.")
                logger.error(msg_erro)
                return None, None, msg_erro
            sucesso_df = log_df[log_df['status'].str.startswith('SUCCESS')]

            # --- 1. OTIMIZAÇÃO CRÍTICA: Filtra apenas arquivos disponíveis em disco ---
            # Isso impede que o Indexador tente abrir arquivos que o antivírus deletou.
            arquivos_disponiveis = set(os.listdir(html_dir))
            df_indexar = sucesso_df[sucesso_df['saved_filename'].isin(
                arquivos_disponiveis)]

            total_docs_log = len(sucesso_df)
            total_docs_indexar = len(df_indexar)
            total_docs_faltando = total_docs_log - total_docs_indexar

            logger.info(
                f"Total de documentos no log (Histórico): {total_docs_log}")
            logger.info(
                f"Total de documentos encontrados e prontos para indexação: {total_docs_indexar}")
            logger.warning(
                f"Total de documentos FALTANTES (deletados/limpos): {total_docs_faltando}")

            if total_docs_indexar == 0:
                msg_erro = "Nenhum arquivo HTML para indexar foi encontrado na pasta temporária. Execute a Etapa 1 (Coleta)."
                logger.error(msg_erro)
                return None, None, msg_erro

            # Itera apenas sobre os documentos que realmente existem
            for doc_id, row in enumerate(df_indexar.itertuples()):
                filepath = os.path.join(html_dir, row.saved_filename)

                # --- 2. TRATAMENTO DE ERRO AO ABRIR ---
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                except OSError as e:
                    # Captura erros de I/O de última hora (improvável com o filtro, mas seguro)
                    logger.error(
                        f"ERRO DE ARQUIVO CRÍTICO (Ignorado): Falha I/O ao ler {row.saved_filename}. Erro: {e}")
                    continue

                tokens = cls.limpar_e_tokenizar(conteudo)
                document_map[doc_id] = row.original_url

                # Frequência de Termos (TF) para o documento atual
                termo_frequencia = defaultdict(int)
                for token in tokens:
                    termo_frequencia[token] += 1

                # Atualizar o índice invertido
                for termo, tf in termo_frequencia.items():
                    # df (Document Frequency): Contagem de documentos que contêm o termo
                    if doc_id not in indice_invertido[termo]['postings']:
                        indice_invertido[termo]['df'] += 1

                    # postings: Armazenamos a Frequência do Termo (TF) para o doc_id
                    indice_invertido[termo]['postings'][doc_id] = tf

            logger.info(
                f"Índice construído. Total de termos únicos: {len(indice_invertido)}")
            # Retorna None para o erro em caso de sucesso
            return indice_invertido, document_map, None

        except Exception as e:
            # Captura falhas na leitura do CSV ou erros de DataFrame
            msg_erro = f"Falha CRÍTICA na construção do índice. Erro: {e}"
            logger.critical(msg_erro)
            return None, None, msg_erro

    @staticmethod
    def salvar_indice(indice, doc_map, output_dir):
        """Salva o índice e o mapa de documentos em formato JSON na pasta de saída."""

        indice_output = os.path.join(output_dir, 'indice_invertido.json')
        map_output = os.path.join(output_dir, 'document_map.json')

        # 1. Salva o Índice Invertido
        with open(indice_output, 'w', encoding='utf-8') as f:
            json.dump(dict(indice), f, ensure_ascii=False, indent=2)

        # 2. Salva o Mapa de Documentos
        with open(map_output, 'w', encoding='utf-8') as f:
            json.dump(doc_map, f, ensure_ascii=False, indent=2)

        logger.info(f"Arquivos do Índice salvos com sucesso em: {output_dir}")
