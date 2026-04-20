import json
import math
import os
import time
import sqlite3
from collections import defaultdict
from logging import getLogger
from functools import lru_cache

# Imports locais - Ajustados para a nova estrutura de pastas
from .Config import DATA_DIR
from .Linguistic import process_text

# --- Definição dos Caminhos dos Artefatos ---
DOCUMENT_MAP_FILE = os.path.join(DATA_DIR, 'document_map.json')
VOCABULARIO_FILE = os.path.join(DATA_DIR, 'vocabulario.json')
POSTINGS_BIN_FILE = os.path.join(DATA_DIR, 'postings.bin')
NORMS_FILE = os.path.join(DATA_DIR, 'norms.json')
# Nova base de dados IDF (Camada WARM)
IDF_DB_FILE = os.path.join(DATA_DIR, 'idf_warm.db')

logger = getLogger('ColetorLogger')


class SearchEngine:
    def __init__(self):
        logger.info(
            "[BACKEND INIT] Inicializando SearchEngine híbrido (RAM/SSD/SQLite)...")

        # 1. Carrega artefatos leves na RAM (Removido o IDF_FILE daqui)
        self.doc_map = self._carregar_json_ram(
            DOCUMENT_MAP_FILE, "Mapa de Documentos")
        self.vocabulario = self._carregar_json_ram(
            VOCABULARIO_FILE, "Vocabulário de Metadados")
        self.doc_norms = self._carregar_json_ram(
            NORMS_FILE, "Normas dos Documentos")

        # 2. Conexão com o Banco IDF (SSD)
        if os.path.exists(IDF_DB_FILE):
            # check_same_thread=False é necessário para o FastAPI (multithread)
            self.idf_conn = sqlite3.connect(
                IDF_DB_FILE, check_same_thread=False)
            logger.info(
                "[BACKEND INIT] Conexão com Banco IDF (SQLite) estabelecida.")
        else:
            logger.critical(
                f"[BACKEND ERROR] Banco IDF não encontrado: {IDF_DB_FILE}")
            raise FileNotFoundError(
                "Execute o script de conversão para gerar o idf_warm.db primeiro.")

        # 3. Abre o arquivo binário de Postings (SSD)
        self.postings_handle = None
        if os.path.exists(POSTINGS_BIN_FILE):
            self.postings_handle = open(POSTINGS_BIN_FILE, 'rb')
            logger.info(
                "[BACKEND INIT] Ponteiro para arquivo binário de Postings aberto.")
        else:
            raise FileNotFoundError(
                f"Arquivo binário não encontrado: {POSTINGS_BIN_FILE}")

        logger.info(
            "[BACKEND INIT] Inicialização concluída. RAM poupada com sucesso.")

    @lru_cache(maxsize=10000)
    def get_idf_weight(self, term):
        """Busca o peso IDF no SQLite com cache para os 10k termos mais usados."""
        try:
            cursor = self.idf_conn.cursor()
            cursor.execute(
                "SELECT weight FROM idf_table WHERE term = ?", (term,))
            result = cursor.fetchone()
            return result[0] if result else 0.0
        except Exception as e:
            logger.error(f"[DB ERROR] Erro ao buscar IDF para '{term}': {e}")
            return 0.0

    def gerar_vetor_consulta_tfidf(self, query_string: str):
        tokens_processados = process_text(query_string)
        if not tokens_processados:
            return {}

        tf_consulta = defaultdict(int)
        for token in tokens_processados:
            tf_consulta[token] += 1

        vetor_tfidf = {}
        for termo, tf in tf_consulta.items():
            # Agora busca no SQLite/Cache em vez de dicionário na RAM
            idf = self.get_idf_weight(termo)
            if idf > 0:
                vetor_tfidf[termo] = tf * idf
        return vetor_tfidf


    def buscar_postings_por_termo(self, termo_processado):
        try:
            cursor = self.idf_conn.cursor()
            # Busca peso, offset e length de uma só vez!
            cursor.execute(
                "SELECT offset, length FROM idf_table WHERE term = ?", (termo_processado,))
            result = cursor.fetchone()

            if not result:
                return None

            offset, length = result
            self.postings_handle.seek(offset)
            bin_data = self.postings_handle.read(length)
            return json.loads(bin_data.decode('utf-8'))
        except Exception as e:
            logger.error(f"[ERROR] Falha no termo '{termo_processado}': {e}")
            return None

    def ranquear_documentos_completo(self, consulta_tfidf: dict):
        start_wall_time = time.time()

        # Foca nos termos mais importantes para não sobrecarregar o I/O
        termos_focados = dict(
            sorted(consulta_tfidf.items(), key=lambda x: x[1], reverse=True)[:20])

        documentos_candidatos = {}
        contagem_termos_por_doc = defaultdict(int)

        for termo in termos_focados.keys():
            postings = self.buscar_postings_por_termo(termo)
            if not postings:
                continue

            idf_termo = self.get_idf_weight(termo)  # Busca indexada
            for doc_id, tf in postings.items():
                contagem_termos_por_doc[doc_id] += 1
                if doc_id not in documentos_candidatos:
                    documentos_candidatos[doc_id] = {}
                documentos_candidatos[doc_id][termo] = tf * idf_termo

        # Cálculo de Similaridade do Cosseno
        norma_query = math.sqrt(sum(p ** 2 for p in consulta_tfidf.values()))
        scores = []

        for doc_id, vetor_doc in documentos_candidatos.items():
            norma_doc = self.doc_norms.get(str(doc_id), 1.0)

            # Numerador: Produto Escalar
            numerador = sum(consulta_tfidf[t] * vetor_doc[t]
                            for t in vetor_doc if t in consulta_tfidf)

            if norma_query > 0 and norma_doc > 0:
                score = numerador / (norma_query * norma_doc)
                if score > 0:
                    scores.append((doc_id, score))

        ranking_ordenado = sorted(scores, key=lambda x: x[1], reverse=True)
        wall_duration = time.time() - start_wall_time
        logger.info(
            f"[RANKING END] Docs: {len(ranking_ordenado)}. Tempo: {wall_duration:.4f}s.")

        return ranking_ordenado

    def __del__(self):
        """Fecha os handles ao destruir o objeto."""
        try:
            if hasattr(self, 'postings_handle') and self.postings_handle:
                self.postings_handle.close()
            if hasattr(self, 'idf_conn') and self.idf_conn:
                self.idf_conn.close()
        except Exception:
            pass

    def _carregar_json_ram(self, path, descricao):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Artefato ausente: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(
                f"[RAM LOAD] {descricao} carregado ({len(data)} entradas).")
            return data

    def buscar(self, query_string: str, pagina: int = 1, resultados_por_pagina: int = 10):
        vetor_query = self.gerar_vetor_consulta_tfidf(query_string)
        if not vetor_query:
            return [], 0

        ranking_completo = self.ranquear_documentos_completo(vetor_query)
        total = len(ranking_completo)

        inicio = (pagina - 1) * resultados_por_pagina
        ranking_paginado = ranking_completo[inicio:inicio +
                                            resultados_por_pagina]

        resultados = []
        for doc_id, score in ranking_paginado:
            url = self.doc_map.get(str(doc_id), "URL não encontrada")
            resultados.append((doc_id, score, url))

        return resultados, total
