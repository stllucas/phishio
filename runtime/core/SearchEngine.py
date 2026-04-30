"""Motor de busca e ranqueamento de documentos."""
import json
import math
import gc
import os
import time
import sqlite3
import ijson
import threading
from collections import defaultdict
from logging import getLogger
from functools import lru_cache

from .Config import DATA_DIR
from .Linguistic import process_text

DOCUMENT_MAP_FILE = os.path.join(DATA_DIR, 'document_map.json')
VOCABULARIO_FILE = os.path.join(DATA_DIR, 'vocabulario.json')
POSTINGS_BIN_FILE = os.path.join(DATA_DIR, 'postings.bin')
NORMS_FILE = os.path.join(DATA_DIR, 'norms.json')
IDF_DB_FILE = os.path.join(DATA_DIR, 'idf_warm.db')

logger = getLogger('ColetorLogger')


class SearchEngine:
    def __init__(self):
        logger.info(
            "[BACKEND INIT] Inicializando SearchEngine híbrido (RAM/SSD/SQLite)...")

        if not os.path.exists(DOCUMENT_MAP_FILE):
            logger.critical(
                f"[BACKEND ERROR] Artefato ausente: {DOCUMENT_MAP_FILE}")
            raise FileNotFoundError(f"Artefato ausente: {DOCUMENT_MAP_FILE}")

        self.doc_norms = self._carregar_json_ram(
            NORMS_FILE, "Normas dos Documentos")
        gc.collect()

        if os.path.exists(IDF_DB_FILE):
            self.idf_conn = sqlite3.connect(
                IDF_DB_FILE, check_same_thread=False)
            logger.info(
                "[BACKEND INIT] Banco de Dados Unificado conectado (SSD).")
        else:
            logger.critical(
                "[BACKEND ERROR] Banco idf_warm.db não encontrado!")
            raise FileNotFoundError("Gere o banco unificado antes de iniciar.")

        if os.path.exists(POSTINGS_BIN_FILE):
            self.postings_handle = open(POSTINGS_BIN_FILE, 'rb')
            self.postings_lock = threading.Lock()
            logger.info(
                "[BACKEND INIT] Acesso ao arquivo de Postings (SSD) OK.")
        else:
            raise FileNotFoundError("Arquivo postings.bin não encontrado.")

        logger.info(
            "[BACKEND INIT] Inicialização concluída com economia de RAM.")

    @lru_cache(maxsize=10000)
    def get_document_url(self, doc_id: str) -> str:
        """Busca a URL de um documento pontualmente e mantém em cache os mais acessados."""
        try:
            with open(DOCUMENT_MAP_FILE, 'rb') as f:
                for key, value in ijson.kvitems(f, ''):
                    if key == str(doc_id):
                        return value
        except Exception as e:
            logger.error(
                f"[MAP ERROR] Erro ao buscar URL para '{doc_id}': {e}")
        return "URL não encontrada"

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
        """Executa o motor de vetorial retornando o vetor contendo os tokens da query recebida."""
        tokens_processados = process_text(query_string)
        if not tokens_processados:
            return {}

        tf_consulta = defaultdict(int)
        for token in tokens_processados:
            tf_consulta[token] += 1

        vetor_tfidf = {}
        for termo, tf in tf_consulta.items():
            idf = self.get_idf_weight(termo)
            if idf > 0:
                vetor_tfidf[termo] = tf * idf
        return vetor_tfidf

    def buscar_postings_por_termo(self, termo_processado):
        try:
            cursor = self.idf_conn.cursor()
            cursor.execute(
                "SELECT offset, length FROM idf_table WHERE term = ?", (termo_processado,))
            result = cursor.fetchone()

            if not result:
                return None

            offset, length = result
            with self.postings_lock:
                self.postings_handle.seek(offset)
                bin_data = self.postings_handle.read(length)
            return json.loads(bin_data.decode('utf-8'))
        except Exception as e:
            logger.error(f"[ERROR] Falha no termo '{termo_processado}': {e}")
            return None

    def ranquear_documentos_completo(self, consulta_tfidf: dict):
        start_wall_time = time.time()

        termos_focados = dict(
            sorted(consulta_tfidf.items(), key=lambda x: x[1], reverse=True)[:20])

        documentos_candidatos = {}
        contagem_termos_por_doc = defaultdict(int)

        for termo in termos_focados.keys():
            postings = self.buscar_postings_por_termo(termo)
            if not postings:
                continue

            idf_termo = self.get_idf_weight(termo)
            for doc_id, tf in postings.items():
                contagem_termos_por_doc[doc_id] += 1
                if doc_id not in documentos_candidatos:
                    documentos_candidatos[doc_id] = {}
                documentos_candidatos[doc_id][termo] = tf * idf_termo

        norma_query = math.sqrt(sum(p ** 2 for p in consulta_tfidf.values()))
        scores = []

        for doc_id, vetor_doc in documentos_candidatos.items():
            norma_doc = self.doc_norms.get(str(doc_id), 1.0)

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
            url = self.get_document_url(str(doc_id))
            resultados.append((doc_id, score, url))

        return resultados, total
