"""Script para converter o arquivo JSON de IDF para um banco de dados SQLite (Camada WARM)."""
import sqlite3
import ijson
import os
from runtime.core.Config import DATA_DIR, IDF_PATH

def converter_idf_para_sqlite():
    db_path = os.path.join(DATA_DIR, "idf_warm.db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS idf_table")
    cursor.execute("CREATE TABLE idf_table (term TEXT PRIMARY KEY, weight REAL)")
    
    print(f"[*] Iniciando conversão de {IDF_PATH}...")
    
    with open(IDF_PATH, 'rb') as f:
        items = ijson.kvitems(f, '')
        batch = []
        count = 0
        
        for term, weight in items:
            batch.append((term, weight))
            
            if len(batch) >= 50000:
                cursor.executemany("INSERT OR IGNORE INTO idf_table VALUES (?, ?)", batch)
                conn.commit()
                count += len(batch)
                print(f"[+] {count} termos inseridos...")
                batch = []
        
        if batch:
            cursor.executemany("INSERT OR IGNORE INTO idf_table VALUES (?, ?)", batch)
            conn.commit()

    print("[*] Criando índice de busca...")
    cursor.execute("CREATE INDEX idx_term ON idf_table(term)")
    conn.commit()
    conn.close()
    print(f"[OK] Banco IDF gerado com sucesso em: {db_path}")

if __name__ == "__main__":
    converter_idf_para_sqlite()
