import firebase_admin
from firebase_admin import credentials, firestore

# 1. Configuração Inicial
cred = credentials.Certificate('tcc-coletor-web-firebase-adminsdk-fbsvc-9a87e2278a.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

def inicializar_usuarios_e_reputacao():
    print("[PHISHIO] Criando coleções de usuários e reputação...")
    
    # --- 1. Coleção: usuarios (Seed de Admins) ---
    admins = [
        {
            'uid': 'zLuq2lRYZodC6OQAGdd8TXIC11i1', 
            'nome': 'Lucas Lima', 
            'email': 'lucasdossantoslima19@gmail.com'
        },
        {
            'uid': 'mxSLZn5WsOhFhWLunMmNG2nMSJ12', 
            'nome': 'Pedro Lückeroth', 
            'email': 'pedroluckeroth@gmail.com'
        }
    ]

    for admin in admins:
        user_ref = db.collection('usuarios').document(admin['uid'])
        user_ref.set({
            'uid': admin['uid'],
            'nome': admin['nome'],
            'email': admin['email'],
            'score_reputacao': 10.0,  # Admin com reputação máxima
            'total_reports': 0,
            'nivel': 'administrador',
            'data_registro': firestore.SERVER_TIMESTAMP
        }, merge=True)
        print(f"Admin configurado: {admin['nome']}")

    # --- 2. Coleção: reputacao_urls (Seed de Exemplo) ---
    # Criando um documento de teste inicial
    reputacao_ref = db.collection('reputacao_urls').document('exemplo_seed')
    reputacao_ref.set({
        'url': 'https://exemplo-seed.com',
        'status': 'analisando',
        'votos_phishing': 0,
        'votos_seguro': 0,
        'ultima_atualizacao': firestore.SERVER_TIMESTAMP
    }, merge=True)

    print("\n[SUCESSO] Estrutura de usuários e reputação inicializada!")

if __name__ == "__main__":
    inicializar_usuarios_e_reputacao()