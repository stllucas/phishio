import ijson
import os
import csv
import json
import time
from multiprocessing import Process, Queue, Value, Lock
from tqdm import tqdm

class TermAudit:
    def __init__(self, json_source='logs/indice_invertido.json', output_dir='provas_unitarias'):
        self.json_source = json_source
        self.output_dir = output_dir
        self.checkpoint_file = 'audit_checkpoint.json'
        
        # Parâmetros de engenharia do TCC [cite: 212]
        self.threshold_pesado = 15000 
        self.num_workers = os.cpu_count() or 4  # Usa todos os núcleos disponíveis
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def carregar_checkpoint(self):
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    return json.load(f).get('ultimo_indice', 0)
            except: return 0
        return 0

    def salvar_checkpoint(self, indice):
        with open(self.checkpoint_file, 'w') as f:
            json.dump({'ultimo_indice': indice}, f)

    def _worker_analise(self, queue):
        """Worker paralelo: Consome da fila e processa a lógica de auditoria."""
        while True:
            item = queue.get()
            if item is None: break # Sinal de parada
            
            termo, dados = item
            # Limpeza para nomes de arquivos seguros
            termo_limpo = "".join([c if c.isalnum() else "_" for c in str(termo)]).strip()
            postings = dados.get('postings', {})
            num_postings = len(postings)

            # Lógica de auditoria para o TCC: identifica termos que excederiam 1MB no Firestore [cite: 210, 215]
            if num_postings > self.threshold_pesado:
                file_path = os.path.join(self.output_dir, f"termoP_{termo_limpo}.csv")
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ID_Documento', 'Frequencia_no_Doc'])
                    for doc_id, freq in postings.items():
                        writer.writerow([doc_id, freq])

    def executar(self):
        inicio = self.carregar_checkpoint()
        print(f"\n[TermAudit] Arquitetura paralela ativada com {self.num_workers} workers.")
        print(f"[INFO] Lendo índice de {self.json_source} a partir de: {inicio}")
        
        # Fila de comunicação entre processos
        queue = Queue(maxsize=1000) 
        workers = []
        
        # Inicia os processos trabalhadores
        for _ in range(self.num_workers):
            p = Process(target=self._worker_analise, args=(queue,))
            p.start()
            workers.append(p)

        total_termos = 0
        barra = tqdm(initial=inicio, desc="Processando Índice")

        try:
            with open(self.json_source, 'r', encoding='utf-8') as f:
                # ijson.kvitems lê o arquivo em pedaços, sem carregar os 4.5GB na RAM [cite: 180]
                objetos = ijson.kvitems(f, '')
                
                for i, (termo, dados) in enumerate(objetos):
                    total_termos += 1
                    
                    if i < inicio:
                        continue
                    
                    # Alimenta a fila para os workers
                    queue.put((termo, dados))
                    
                    if i % 1000 == 0:
                        self.salvar_checkpoint(i)
                        barra.update(1000)
                        
        except KeyboardInterrupt:
            print("\n[AVISO] Processamento interrompido. Checkpoint salvo.")
        finally:
            # Envia sinal de encerramento para todos os workers
            for _ in range(self.num_workers): 
                queue.put(None)
            
            for p in workers: 
                p.join()
            
            barra.close()
            self.salvar_checkpoint(total_termos)
            
            print("\n" + "="*50)
            print(f"AUDITORIA FINALIZADA")
            print(f"Total de termos no índice invertido: {total_termos}")
            print(f"Pasta de evidências: {self.output_dir}")
            print("="*50)

if __name__ == "__main__":
    auditoria = TermAudit()
    auditoria.executar()