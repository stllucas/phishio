"""Script para inicializar as coleções de usuários e reputação inicial no Firestore."""
import firebase_admin
from firebase_admin import credentials, firestore
import runtime.core.Config as Config

cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)
db = firestore.client()

def inicializar_usuarios_e_reputacao():
    print("[PHISHIO] Criando coleções de usuários e reputação...")
    
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
            'score_reputacao': 10.0,
            'total_reports': 0,
            'nivel': 'administrador',
            'data_registro': firestore.SERVER_TIMESTAMP
        }, merge=True)
        print(f"Admin configurado: {admin['nome']}")

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