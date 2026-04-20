import sqlite3
import ijson
import os
from runtime.core.Config import DATA_DIR, IDF_PATH, VOCAB_PATH


def converter_indice_completo():
    db_path = os.path.join(DATA_DIR, "idf_warm.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS idf_table")
    # Tabela unificada: termo, peso, posição no binário e tamanho
    cursor.execute("""
        CREATE TABLE idf_table (
            term TEXT PRIMARY KEY, 
            weight REAL, 
            offset INTEGER, 
            length INTEGER
        )
    """)

    print("[*] Lendo pesos IDF e Vocabulário simultaneamente...")

    # Carregamos o vocabulário (metadados) primeiro para cruzar dados
    # Se o vocabulario.json for muito grande para abrir aqui, usaremos ijson também
    with open(IDF_PATH, 'rb') as f_idf, open(VOCAB_PATH, 'rb') as f_vocab:
        idf_items = ijson.kvitems(f_idf, '')
        vocab_items = ijson.kvitems(f_vocab, '')

        # Como ambos são ordenados ou mapeiam os mesmos termos, vamos iterar
        # Dica: Se forem muitos, o ideal é inserir o vocab primeiro e dar UPDATE com o IDF
        print("[*] Inserindo Vocabulário e IDF no banco...")
        batch = []
        # Para performance, vamos carregar o vocab em um dicionário temporário
        # SE ele couber. Se não, faremos dois passes.
        # Vamos assumir o caminho mais seguro para 4GB: Dois passes.

        # Passo 1: Inserir Termo + Offset + Length
        print("[1/2] Gravando metadados do SSD...")
        for term, meta in vocab_items:
            batch.append((term, 0.0, meta['offset'], meta['length']))
            if len(batch) >= 50000:
                cursor.executemany(
                    "INSERT OR IGNORE INTO idf_table VALUES (?, ?, ?, ?)", batch)
                conn.commit()
                batch = []
        if batch:
            cursor.executemany(
                "INSERT OR IGNORE INTO idf_table VALUES (?, ?, ?, ?)", batch)
            conn.commit()

        # Passo 2: Atualizar os pesos IDF
        print("[2/2] Atualizando pesos estatísticos...")
        batch = []
        for term, weight in idf_items:
            batch.append((float(weight), term))
            if len(batch) >= 50000:
                cursor.executemany(
                    "UPDATE idf_table SET weight = ? WHERE term = ?", batch)
                conn.commit()
                batch = []
        if batch:
            cursor.executemany(
                "UPDATE idf_table SET weight = ? WHERE term = ?", batch)
            conn.commit()

    cursor.execute("CREATE INDEX idx_term ON idf_table(term)")
    conn.commit()
    conn.close()
    print("[OK] Banco Unificado gerado!")


if __name__ == "__main__":
    converter_indice_completo()
