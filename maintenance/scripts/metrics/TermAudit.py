"""Script para auditoria de termos e identificação de anomalias no índice invertido."""
import ijson
import os
import csv
import json
from multiprocessing import Process, Queue, Lock
from tqdm import tqdm


class TermAudit:
    def __init__(self, json_source='logs/indice_invertido.json', output_dir='provas_unitarias'):
        self.json_source = json_source
        self.output_dir = output_dir
        self.checkpoint_file = 'audit_checkpoint.json'
        self.output_file = os.path.join(self.output_dir, 'anomalous_terms.csv')

        self.threshold_pesado = 15000
        self.num_workers = os.cpu_count() or 4

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def carregar_checkpoint(self):
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    return json.load(f).get('ultimo_indice', 0)
            except (json.JSONDecodeError, OSError):
                return 0
        return 0

    def salvar_checkpoint(self, indice):
        with open(self.checkpoint_file, 'w') as f:
            json.dump({'ultimo_indice': indice}, f)

    def _worker_analise(self, queue, lock):
        """Worker paralelo: Consome da fila e processa a lógica de auditoria."""
        while True:
            item = queue.get()
            if item is None:
                break

            termo, dados = item
            postings = dados.get('postings', {})
            num_postings = len(postings)

            if num_postings > self.threshold_pesado:
                rows = [[termo, doc_id, freq] for doc_id, freq in postings.items()]
                with lock:
                    with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerows(rows)

    def executar(self):
        inicio = self.carregar_checkpoint()
        print(
            f"\n[TermAudit] Arquitetura paralela ativada com {self.num_workers} workers.")
        print(
            f"[INFO] Lendo índice de {self.json_source} a partir de: {inicio}")

        if inicio == 0 or not os.path.exists(self.output_file):
            with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Termo', 'ID_Documento', 'Frequencia_no_Doc'])

        queue = Queue(maxsize=1000)
        lock = Lock()
        workers = []

        for _ in range(self.num_workers):
            p = Process(target=self._worker_analise, args=(queue, lock))
            p.start()
            workers.append(p)

        total_termos = 0
        barra = tqdm(initial=inicio, desc="Processando Índice")

        try:
            with open(self.json_source, 'r', encoding='utf-8') as f:
                objetos = ijson.kvitems(f, '')

                for i, (termo, dados) in enumerate(objetos):
                    total_termos += 1

                    if i < inicio:
                        continue

                    queue.put((termo, dados))

                    if i % 1000 == 0:
                        self.salvar_checkpoint(i)
                        barra.update(1000)

        except KeyboardInterrupt:
            print("\n[AVISO] Processamento interrompido. Checkpoint salvo.")
        finally:
            for _ in range(self.num_workers):
                queue.put(None)

            for p in workers:
                p.join()

            barra.close()
            self.salvar_checkpoint(total_termos)

            print("\n" + "="*50)
            print("AUDITORIA FINALIZADA")
            print(f"Total de termos no índice invertido: {total_termos}")
            print(f"Pasta de evidências: {self.output_dir}")
            print("="*50)


if __name__ == "__main__":
    auditoria = TermAudit()
    auditoria.executar()
