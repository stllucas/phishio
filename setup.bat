REM Script de inicializacao e configuracao do ambiente Phishio para Windows.
@echo off
chcp 65001 > nul

echo [1/6] Criando Ambiente Virtual (venv)...
if exist venv\ goto :VenvExists
py -m venv venv
if not exist venv\Scripts\activate.bat goto :VenvError
echo [OK] Ambiente virtual 'venv' criado com sucesso.
goto :Step2

:VenvExists
echo [INFO] Ambiente virtual 'venv' ja existe. Pulando criacao.
goto :Step2

:VenvError
echo.
echo ==============================================================
echo [ERRO CRITICO] Falha ao criar o ambiente virtual.
echo Verifique se o Python esta instalado e adicionado ao PATH do Windows.
echo ==============================================================
pause
exit /b 1

:Step2
echo.
echo [2/6] Ativando ambiente virtual...
call .\venv\Scripts\activate

echo.
echo [3/6] Atualizando o PIP...
python.exe -m pip install --upgrade pip

echo.
echo [4/6] Instalando dependências do projeto...
if exist "requirements.txt" (
  echo [INFO] Instalando pacotes via requirements.txt...
  pip install -r requirements.txt
  ) else (
  echo [ERRO] requirements.txt não encontrado na raiz do projeto.
  pause
  exit /b 1
)

echo.
echo [5/6] Baixando recursos do NLTK...
python -m nltk.downloader -q stopwords punkt
echo [OK] Dados linguisticos verificados/baixados.

echo.
echo [6/6] Verificando necessidade de migracao de indice (Otimizacao RAM/SSD)...

set "INDICE_JSON=backend\logs\indice_invertido.json"
set "POSTINGS_BIN=backend\logs\postings.bin"
set "MIGRATION_SCRIPT=scripts\data_prep\MigrarIndice.py"

if not exist "%INDICE_JSON%" goto :SkipMigrationSourceMissing

if exist "%POSTINGS_BIN%" goto :SkipMigrationAlreadyDone

if not exist "%MIGRATION_SCRIPT%" goto :SkipMigrationScriptMissing

echo [INFO] Arquivo de indice monolitico encontrado.
echo [INFO] Iniciando migracao automatica para formato otimizado (Isso pode demorar)...
echo.
py "%MIGRATION_SCRIPT%"
goto :MigrationEnd

:SkipMigrationAlreadyDone
echo [INFO] O indice ja esta migrado e otimizado para SSD. Pulando etapa.
goto :MigrationEnd

:SkipMigrationSourceMissing
echo [AVISO] '%INDICE_JSON%' nao encontrado.
echo Se esta for uma instalacao limpa, voce precisara rodar os scripts de coleta primeiro.
goto :MigrationEnd

:SkipMigrationScriptMissing
echo [AVISO] Script de migracao '%MIGRATION_SCRIPT%' nao encontrado na pasta scripts.
echo A migracao automatica foi pulada.
goto :MigrationEnd

:MigrationEnd
echo.
echo ==========================================================
echo AMBIENTE PHISHIO ATUALIZADO E CONFIGURADO COM SUCESSO!
echo ==========================================================
echo.
echo [COMO INICIAR A SUA API / BACK-END]
echo  1. Digite no terminal:  .\venv\Scripts\activate
echo  2. Navegue ate a pasta: cd backend
echo  3. Inicie o servidor:  py -m uvicorn main:app --reload
echo.
echo [COMO TESTAR A EXTENSAO / FRONT-END]
echo  1. Abra o Chrome e acesse a URL: chrome://extensions/
echo  2. Ative o "Modo do desenvolvedor" (canto superior direito).
echo  3. Clique em "Carregar sem compactacao" e selecione a pasta 'extension' deste projeto.
echo.
echo Para mais informacoes, consulte o arquivo README.md
echo.

pause
cls
