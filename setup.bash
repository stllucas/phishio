#!/bin/bash

# =================================================================
# Script de Setup, Instalacao e Atualizacao de Dependencias (Linux)
# PROJETO PHISHIO - ARQUITETURA MONOREPO
# =================================================================

echo "[1/6] Preparando Ambiente Virtual (venv)..."
# No Linux, o comando de criação é python3
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "[OK] Ambiente virtual 'venv' criado."
else
    echo "[INFO] Ambiente virtual 'venv' ja existe."
fi

# --- PASSO 2 ---
echo -e "\n[2/6] Ativando ambiente virtual..."
# No Linux, o caminho de ativação é bin/activate
source ./venv/bin/activate

# --- PASSO 3 ---
echo -e "\n[3/6] Atualizando o PIP..."
pip install --upgrade pip

# --- PASSO 4 ---
echo -e "\n[4/6] Instalando dependencias do projeto..."
if [ -f "requirements.txt" ]; then
    echo "[INFO] Usando requirements.txt da raiz."
    pip install --upgrade -r requirements.txt
else
    echo "[INFO] requirements.txt nao encontrado. Instalando manualmente..."
    pip install --upgrade fastapi uvicorn google-cloud-firestore pandas requests tqdm beautifulsoup4 nltk ijson firebase-admin
fi

# --- PASSO 5 ---
echo -e "\n[5/6] Baixando dados linguisticos do NLTK..."
python3 -m nltk.downloader -q stopwords punkt
echo "[OK] Dados linguisticos verificados."

# --- PASSO 6 ---
echo -e "\n[6/6] Verificando migracao de indice (Otimizacao)..."
# Adaptando caminhos para o padrão Linux/Posix
INDICE_JSON="backend/logs/indice_invertido.json"
POSTINGS_BIN="backend/logs/postings.bin"
MIGRATION_SCRIPT="scripts/data_prep/MigrarIndice.py"

if [ ! -f "$INDICE_JSON" ]; then
    echo "[AVISO] Arquivo de indice fonte nao encontrado."
elif [ -f "$POSTINGS_BIN" ]; then
    echo "[INFO] O indice ja esta otimizado. Pulando."
elif [ ! -f "$MIGRATION_SCRIPT" ]; then
    echo "[AVISO] Script de migracao nao encontrado."
else
    echo "[INFO] Iniciando migracao automatica..."
    python3 "$MIGRATION_SCRIPT"
fi

echo "\n=========================================================="
echo "AMBIENTE PHISHIO (LINUX) CONFIGURADO COM SUCESSO!"
echo "=========================================================="
echo"."
echo "[COMO INICIAR A SUA API / BACK-END]"
echo "  1. Digite no terminal:  .\venv\Scripts\activate"
echo "  2. Navegue ate a pasta: cd backend"
echo "  3. Inicie o servidor:   py -m uvicorn main:app --reload"
echo"."
echo "[COMO TESTAR A EXTENSAO / FRONT-END]"
echo "  1. Abra o Chrome e acesse a URL: chrome://extensions/"
echo "  2. Ative o "'Modo do desenvolvedo'" (canto superior direito)."
echo "  3. Clique em "'Carregar sem compactaca'" e selecione a pasta 'extension' deste projeto."
echo"."
echo "[MANUTENCAO DO PROJETO]"
echo   "Lembre-se: Caso novos pacotes ou dependencias sejam usados no projeto,"
echo   "eles devem ser inseridos no arquivo 'requirements.txt'."
echo   "Isso garante que o ambiente seja instalado corretamente por todos."
echo"."
echo "Para mais informacoes, consulte o arquivo README.md"
echo -e "."

break
