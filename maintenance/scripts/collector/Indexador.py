"""Módulo responsável pela Representação e Indexação dos dados coletados."""
import heapq
import json
import os
import re
import shutil
import tempfile
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
except LookupError as e:
    STOPWORDS = None
    STEMMER = None
    logger.error(f"Falha ao carregar recursos do NLTK: {e}. A indexação não poderá prosseguir corretamente.")


class Indexador:
    """
    Constrói e salva o Índice Invertido a partir dos arquivos HTML coletados.
    """

    @staticmethod
    def _remover_tags_e_obter_texto(conteudo_html):
        """Usa BeautifulSoup para remover tags de estrutura (scripts/styles) e obter o texto visível."""
        try:
            soup = BeautifulSoup(conteudo_html, 'html.parser')

            for script_or_style in soup(['script', 'style']):
                script_or_style.decompose()

            return soup.get_text(separator=' ')
        except Exception as e:
            logger.error(f"Erro na BeautifulSoup ao processar HTML. {e}")
            return ""

    @classmethod
    def limpar_e_tokenizar(cls, conteudo_html):
        """Aplica análise léxica: limpeza, tokenização, remoção de stopwords e stemming."""
        if STOPWORDS is None or STEMMER is None:
            raise RuntimeError("Recursos linguísticos do NLTK não estão disponíveis.")

        texto_limpo = cls._remover_tags_e_obter_texto(conteudo_html)

        limpo = re.sub(
            r'[^a-zA-ZáéíóúàèìòùãõâêîôûçÁÉÍÓÚÀÈÌÒÙÃÕÂÊÎÔÛÇ\s]', '', texto_limpo).lower()

        tokens = limpo.split()

        tokens_processados = []
        for token in tokens:
            if token not in STOPWORDS and len(token) > 2:
                tokens_processados.append(STEMMER.stem(token))

        return tokens_processados

    @classmethod
    def construir_indice_invertido(cls, log_file_path, html_dir, block_size=2000):
        """
        Lê o log de sucesso e os arquivos HTML DISPONÍVEIS para construir o índice invertido
        utilizando processamento em blocos no disco (SPIMI) para evitar sobrecarga na memória RAM.
        """

        logger.info("Iniciando construção do Índice Invertido...")

        document_map = {}

        try:
            log_df = pd.read_csv(
                log_file_path, on_bad_lines='skip', low_memory=False, engine='python', quotechar='"'
            )

            colunas_necessarias = {'status', 'saved_filename', 'original_url'}
            if log_df.empty or not colunas_necessarias.issubset(log_df.columns):
                msg_erro = ("O arquivo de log ('collection_log.csv') está vazio ou malformado. "
                            "Execute a Etapa 1 (Coleta) primeiro para gerar um log válido.")
                logger.error(msg_erro)
                return None, None, msg_erro
            sucesso_df = log_df[log_df['status'].str.startswith('SUCCESS')]

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

            temp_dir = tempfile.mkdtemp(prefix="phishio_index_blocks_")
            block_id = 0
            current_block = defaultdict(lambda: {'df': 0, 'postings': {}})
            docs_in_block = 0

            def save_block():
                nonlocal block_id, current_block, docs_in_block
                if not current_block:
                    return
                block_path = os.path.join(temp_dir, f"block_{block_id}.jsonl")
                with open(block_path, 'w', encoding='utf-8') as bf:
                    for termo in sorted(current_block.keys()):
                        record = {termo: current_block[termo]}
                        bf.write(json.dumps(record, ensure_ascii=False) + '\n')

                logger.info(
                    f"Bloco {block_id} salvo no disco com {docs_in_block} documentos e {len(current_block)} termos.")

                block_id += 1
                current_block.clear()
                docs_in_block = 0

            for doc_id, row in enumerate(df_indexar.itertuples()):
                filepath = os.path.join(html_dir, row.saved_filename)

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                except OSError as e:
                    logger.error(
                        f"ERRO DE ARQUIVO CRÍTICO (Ignorado): Falha I/O ao ler {row.saved_filename}. Erro: {e}")
                    continue

                try:
                    tokens = cls.limpar_e_tokenizar(conteudo)
                except Exception as e:
                    logger.error(f"Falha na biblioteca linguística ao processar HTML {row.saved_filename}: {e}. Arquivo ignorado.")
                    continue

                document_map[doc_id] = row.original_url

                termo_frequencia = defaultdict(int)
                for token in tokens:
                    termo_frequencia[token] += 1

                for termo, tf in termo_frequencia.items():
                    if doc_id not in current_block[termo]['postings']:
                        current_block[termo]['df'] += 1
                    current_block[termo]['postings'][doc_id] = tf

                docs_in_block += 1
                if docs_in_block >= block_size:
                    save_block()

            if docs_in_block > 0:
                save_block()

            logger.info("Iniciando merge dos blocos no disco...")
            merged_index_path = os.path.join(temp_dir, "merged_index.json")

            block_files = [open(os.path.join(
                temp_dir, f"block_{i}.jsonl"), 'r', encoding='utf-8') for i in range(block_id)]

            def block_reader(f, b_id):
                for line in f:
                    yield json.loads(line), b_id

            pq = []
            readers = []
            for i, f in enumerate(block_files):
                reader = block_reader(f, i)
                readers.append(reader)
                try:
                    record, _ = next(reader)
                    term = list(record.keys())[0]
                    data = record[term]
                    heapq.heappush(pq, (term, i, data))
                except StopIteration:
                    pass

            total_termos = 0
            with open(merged_index_path, 'w', encoding='utf-8') as out_f:
                out_f.write("{\n")

                current_term = None
                current_data = {'df': 0, 'postings': {}}
                first_term = True

                while pq:
                    term, b_id, data = heapq.heappop(pq)

                    if current_term is None:
                        current_term = term

                    if term == current_term:
                        current_data['df'] += data['df']
                        current_data['postings'].update(data['postings'])
                    else:
                        if not first_term:
                            out_f.write(",\n")
                        out_f.write(
                            f'  "{current_term}": {json.dumps(current_data, ensure_ascii=False)}')
                        first_term = False
                        total_termos += 1

                        current_term = term
                        current_data = {
                            'df': data['df'], 'postings': data['postings']}

                    try:
                        record, _ = next(readers[b_id])
                        next_term = list(record.keys())[0]
                        next_data = record[next_term]
                        heapq.heappush(pq, (next_term, b_id, next_data))
                    except StopIteration:
                        pass

                if current_term is not None:
                    if not first_term:
                        out_f.write(",\n")
                    out_f.write(
                        f'  "{current_term}": {json.dumps(current_data, ensure_ascii=False)}\n')
                    total_termos += 1

                out_f.write("}\n")

            for f in block_files:
                f.close()
            for i in range(block_id):
                os.remove(os.path.join(temp_dir, f"block_{i}.jsonl"))

            logger.info(
                f"Índice construído e unificado. Total de termos únicos: {total_termos}")
            return merged_index_path, document_map, None

        except Exception as e:
            msg_erro = f"Falha CRÍTICA na construção do índice. Erro: {e}"
            logger.critical(msg_erro)
            return None, None, msg_erro

    @staticmethod
    def salvar_indice(indice, doc_map, output_dir):
        """Salva o índice e o mapa de documentos em formato JSON na pasta de saída."""

        indice_output = os.path.join(output_dir, 'indice_invertido.json')
        map_output = os.path.join(output_dir, 'document_map.json')

        if isinstance(indice, str) and os.path.exists(indice):
            shutil.move(indice, indice_output)
            temp_dir = os.path.dirname(indice)
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass
        else:
            with open(indice_output, 'w', encoding='utf-8') as f:
                json.dump(dict(indice), f, ensure_ascii=False, indent=2)

        with open(map_output, 'w', encoding='utf-8') as f:
            json.dump(doc_map, f, ensure_ascii=False, indent=2)

        logger.info(f"Arquivos do Índice salvos com sucesso em: {output_dir}")
