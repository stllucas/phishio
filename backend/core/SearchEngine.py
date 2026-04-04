# ==============================================================================
# src/SearchEngine.py
# Módulo principal da Etapa 3, responsável pela busca, ranking e mapeamento.
# Utiliza arquitetura híbrida RAM/SSD e registra detalhes de execução.
# ==============================================================================
import json
import math
import os
import time # Importante para cronometrar o backend
import gc
from logging import getLogger
from collections import defaultdict
from .linguistic import process_text
from .Config import LOG_DIR_OUTPUT

# --- Definição dos Caminhos dos Artefatos ---
DOCUMENT_MAP_FILE = os.path.join(LOG_DIR_OUTPUT, 'document_map.json')
IDF_FILE = os.path.join(LOG_DIR_OUTPUT, 'idf.json')
VOCABULARIO_FILE = os.path.join(LOG_DIR_OUTPUT, 'vocabulario.json') # RAM
POSTINGS_BIN_FILE = os.path.join(LOG_DIR_OUTPUT, 'postings.bin')   # SSD

logger = getLogger('ColetorLogger')

class SearchEngine:
    """
    Motor de Busca Otimizado com Suporte a Paginação e Logs Detalhados.
    """
    def __init__(self):
        logger.info("[BACKEND INIT] Inicializando SearchEngine híbrido (RAM/SSD)...")
        
        # 1. Carrega artefatos leves na RAM
        self.doc_map = self._carregar_json_ram(DOCUMENT_MAP_FILE, "Mapa de Documentos")
        self.idf_map = self._carregar_json_ram(IDF_FILE, "Mapa IDF global")
        self.vocabulario = self._carregar_json_ram(VOCABULARIO_FILE, "Vocabulário de Metadados")

        # 2. Abre o arquivo binário gigante no SSD
        self.postings_handle = None
        if os.path.exists(POSTINGS_BIN_FILE):
            try:
                self.postings_handle = open(POSTINGS_BIN_FILE, 'rb')
                logger.info(f"[BACKEND INIT] Ponteiro para arquivo binário no SSD aberto com sucesso.")
            except Exception as e:
                logger.critical(f"[BACKEND ERROR] Falha ao abrir arquivo binário no SSD: {e}")
                raise
        else:
            logger.critical(f"[BACKEND ERROR] Arquivo binário SSD não encontrado: {POSTINGS_BIN_FILE}")
            raise

        logger.info("[BACKEND INIT] Inicialização concluída. Pronto para consultas.")

    # ... (Métodos __del__, liberar_memoria_explicitamente e _carregar_json_ram) ...
    def __del__(self):
        if self.postings_handle:
            try: self.postings_handle.close()
            except: pass

    def liberar_memoria_explicitamente(self):
        logger.info("[BACKEND SHUTDOWN] Iniciando liberação explícita de memória...")
        if self.postings_handle:
            try:
                self.postings_handle.close()
                logger.info("[BACKEND SHUTDOWN] Arquivo SSD fechado.")
            except: pass
            self.postings_handle = None
        self.doc_map = None
        self.idf_map = None
        self.vocabulario = None
        collected = gc.collect()
        logger.info(f"[BACKEND SHUTDOWN] Limpeza concluída. Garbage Collector liberou {collected} objetos da RAM.")

    def _carregar_json_ram(self, path, descricao):
        if not os.path.exists(path):
             logger.critical(f"[BACKEND ERROR] Artefato obrigatório não encontrado: {path}")
             return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"[RAM LOAD] {descricao} carregado na memória ({len(data)} entradas).")
            return data
        except Exception as e:
             logger.critical(f"[RAM LOAD ERROR] Erro ao carregar {descricao}: {e}")
             return {}

    # ... (Métodos _processar_texto_query e gerar_vetor_consulta_tfidf) ...
    # O método _processar_texto_query foi removido e substituído pela importação de process_text
    
    def gerar_vetor_consulta_tfidf(self, query_string: str):
        tokens_processados = process_text(query_string)
        if not tokens_processados: return {}
        tf_consulta = defaultdict(int)
        for token in tokens_processados:
            tf_consulta[token] += 1
        vetor_tfidf = {}
        for termo, tf in tf_consulta.items():
            idf = self.idf_map.get(termo, 0)
            if idf > 0:
                vetor_tfidf[termo] = tf * idf
        return vetor_tfidf

    # ==========================================================================
    # MÉTODOS COM LOGS TÉCNICOS APRIMORADOS
    # ==========================================================================
    
    def buscar_postings_por_termo(self, termo_processado):
        """Busca no SSD com log explícito da operação de I/O."""
        metadata = self.vocabulario.get(termo_processado)
        if not metadata: return None
        
        offset = metadata.get('offset')
        length = metadata.get('length')
        if offset is None or length is None: return None

        try:
            # Registra o acesso cirúrgico ao SSD
            logger.debug(f"[SSD I/O] Realizando seek/read para o termo '{termo_processado}' (Offset: {offset}, Bytes: {length})")
            
            self.postings_handle.seek(offset)
            bin_data = self.postings_handle.read(length)
            postings_dict_str = bin_data.decode('utf-8')
            postings_dict = json.loads(postings_dict_str)
            return {int(k): v for k, v in postings_dict.items()}
        except Exception as e:
             logger.error(f"[SSD I/O ERROR] Falha ao ler postings para '{termo_processado}': {e}")
             return None

    def mapear_resultados_para_urls(self, doc_ids: list):
        if not self.doc_map: return []
        urls_ranqueadas = []
        for doc_id in doc_ids:
            url = self.doc_map.get(str(doc_id))
            if url: urls_ranqueadas.append(url)
        return urls_ranqueadas

    @staticmethod
    def similaridade_cosseno(vetor1: dict, vetor2: dict) -> float:
        # (Cálculo matemático puro)
        numerador = sum(vetor1[t] * vetor2[t] for t in vetor1 if t in vetor2)
        norma1 = math.sqrt(sum(p ** 2 for p in vetor1.values()))
        norma2 = math.sqrt(sum(p ** 2 for p in vetor2.values()))
        if norma1 == 0 or norma2 == 0: return 0.0
        return numerador / (norma1 * norma2)

    def ranquear_documentos_completo(self, consulta_tfidf: dict):
        """
        Realiza o ranking completo com logs do mecanismo e tempo de processamento.
        """
        # Registra o início e o método de ranking
        logger.info(f"[RANKING START] Iniciando ranking vetorial (Mecanismo: TF-IDF + Similaridade do Cosseno). Termos na consulta: {len(consulta_tfidf)}")
        
        # Cronometra o tempo de processamento interno
        start_cpu_time = time.process_time()
        start_wall_time = time.time()

        documentos_candidatos = {}

        # 1. Fase de Recuperação (SSD -> RAM)
        logger.info("[RANKING PHASE 1] Recuperando postings lists do SSD...")
        termos_recuperados = 0
        for termo in consulta_tfidf.keys():
            postings = self.buscar_postings_por_termo(termo)
            if not postings: continue
            termos_recuperados += 1
            idf_termo = self.idf_map.get(termo, 0)
            for doc_id, tf in postings.items():
                if doc_id not in documentos_candidatos:
                    documentos_candidatos[doc_id] = {}
                documentos_candidatos[doc_id][termo] = tf * idf_termo

        if not documentos_candidatos:
            logger.info("[RANKING END] Nenhum documento candidato encontrado nas postings lists.")
            return []

        # 2. Fase de Cálculo de Similaridade (RAM)
        logger.info(f"[RANKING PHASE 2] Calculando similaridade na RAM para {len(documentos_candidatos)} documentos candidatos...")
        scores = []
        for doc_id, vetor_doc in documentos_candidatos.items():
            score = self.similaridade_cosseno(consulta_tfidf, vetor_doc)
            if score > 0:
                scores.append((doc_id, score))

        # 3. Ordenação Completa
        ranking_ordenado = sorted(scores, key=lambda x: x[1], reverse=True)
        
        end_cpu_time = time.process_time()
        end_wall_time = time.time()
        cpu_duration = end_cpu_time - start_cpu_time
        wall_duration = end_wall_time - start_wall_time
        
        # Resumo final do processamento do backend
        logger.info(f"[RANKING END] Concluído. Docs ranqueados: {len(ranking_ordenado)}. Tempo Backend (Wall): {wall_duration:.4f}s, (CPU): {cpu_duration:.4f}s.")
        logger.info(f"[RANKING SUMMARY] Dados recuperados do SSD (Postings de {termos_recuperados} termos) e processados na RAM (Vetores e Cosseno).")
        
        return ranking_ordenado

    def buscar(self, query_string: str, pagina: int = 1, resultados_por_pagina: int = 10):
        # (Método fachada, a lógica pesada está no ranquear_documentos_completo)
        vetor_query = self.gerar_vetor_consulta_tfidf(query_string)
        if not vetor_query: return [], 0
        
        ranking_completo = self.ranquear_documentos_completo(vetor_query)
        total_resultados = len(ranking_completo)
        
        if total_resultados == 0:
            return [], 0
            
        inicio = (pagina - 1) * resultados_por_pagina
        fim = inicio + resultados_por_pagina
        ranking_paginado = ranking_completo[inicio:fim]
        
        doc_ids_pagina = [doc_id for doc_id, score in ranking_paginado]
        urls_pagina = self.mapear_resultados_para_urls(doc_ids_pagina)
        
        resultados_finais_pagina = []
        for i in range(len(ranking_paginado)):
             resultados_finais_pagina.append((ranking_paginado[i][0], ranking_paginado[i][1], urls_pagina[i]))
             
        return resultados_finais_pagina, total_resultados