#!/bin/bash

# =================================================================
# Script de Setup, Instalacao e Atualizacao de Dependencias (LINUX)
# PROJETO PHISHIO - ARQUITETURA TIERED STORAGE
# =================================================================

echo "----------------------------------------------------------"
echo "PHISHIO - AMBIENTE DE PRODUCAO/MANUTENCAO"
echo "----------------------------------------------------------"

# --- PASSO 1: VENV ---
echo "[1/6] Preparando Ambiente Virtual (venv)..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "[OK] Ambiente virtual 'venv' criado."
else
    echo "[INFO] Ambiente virtual 'venv' ja existe."
fi

# --- PASSO 2: ATIVACAO ---
echo -e "\n[2/6] Ativando ambiente virtual..."
source ./venv/bin/activate

# --- PASSO 3: PIP ---
echo -e "\n[3/6] Atualizando o PIP..."
pip install --upgrade pip

# --- PASSO 4: DEPENDENCIAS ---
echo -e "\n[4/6] Instalando dependencias do projeto..."
# Prioriza o requirements da raiz, senao instala o core
if [ -f "requirements.txt" ]; then
    pip install --upgrade -r requirements.txt
else
    echo "[AVISO] requirements.txt nao encontrado. Instalando pacotes base..."
    pip install --upgrade fastapi uvicorn google-cloud-firestore beautifulsoup4 nltk tqdm ijson
fi

# --- PASSO 5: NLTK ---
echo -e "\n[5/6] Baixando dados linguisticos do NLTK..."
python3 -m nltk.downloader -q stopwords punkt
echo "[OK] Dados linguisticos verificados."

# --- PASSO 6: MIGRACAO (Ajustado para Tiered Storage) ---
echo -e "\n[6/6] Verificando integridade dos dados (Camada Warm)..."
# Novos caminhos conforme a nossa reestruturacao
INDICE_FONTE="maintenance/data-raw/indice_invertido.json"
POSTINGS_BIN="data/postings.bin"
MIGRATION_SCRIPT="maintenance/scripts/database/MigrarIndice.py"

if [ ! -f "$INDICE_FONTE" ]; then
    echo "[INFO] Indice fonte (4.6GB) nao detectado localmente. Pulando migracao."
elif [ -f "$POSTINGS_BIN" ]; then
    echo "[INFO] Artefato binario ja existe em data/. Pronto para uso."
elif [ ! -f "$MIGRATION_SCRIPT" ]; then
    echo "[ERRO] Script de migracao nao encontrado em maintenance/."
else
    echo "[ALERTA] Indice binario faltando. Iniciando conversao..."
    python3 "$MIGRATION_SCRIPT"
fi

echo -e "\n=========================================================="
echo "      AMBIENTE CONFIGURADO COM SUCESSO (LINUX VM)         "
echo "=========================================================="
echo -e "\n[COMO INICIAR O BACKEND]"
echo "  1. Ative o venv:    source venv/bin/activate"
echo "  2. Entre na pasta:  cd runtime"
echo "  3. Rode a API:      python3 -m uvicorn main:app --host 0.0.0.0 --port 8000"
echo -e "\n[DICA DE PRODUCAO]"
echo "  Para manter a API rodando apos fechar o SSH, use:"
echo "  nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &"
echo "----------------------------------------------------------"