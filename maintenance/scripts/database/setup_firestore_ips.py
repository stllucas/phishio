import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from zoneinfo import ZoneInfo

# Imports internos
from runtime.core.Config import SECRETS_FILE
# Ajuste o caminho do secrets conforme o seu servidor
secrets_path = SECRETS_FILE
cred = credentials.Certificate(secrets_path)
firebase_admin.initialize_app(cred)

db = firestore.client()

def init_ip_collection():
    print("Iniciando criação da coleção de Mapemanento Geográfico...")
    
    # Documento de semente (seed) para validar a estrutura
    seed_data = {
        "url": "http://teste-inicial-banco.com",
        "user_id": "system_init_001",
        "ip": "200.147.67.142", # Exemplo de IP do UOL (Brasil)
        "estado": "Minas Gerais",
        "cidade": "Belo Horizonte",
        "pais": "Brazil",
        "timestamp": datetime.now(ZoneInfo("America/Sao_Paulo"))
    }
    
    doc_ref = db.collection("reports_geolocalizados").document("seed_init")
    doc_ref.set(seed_data)
    
    print(f"Coleção 'reports_geolocalizados' criada com sucesso. Seed ID: {doc_ref.id}")

if __name__ == "__main__":
    init_ip_collection()