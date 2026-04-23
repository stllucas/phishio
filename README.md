# O phishio

**Phishio** é um sistema híbrido para detecção de *phishing* em tempo real, desenvolvido como um **Trabalho de Conclusão de Curso (TCC)**.

O projeto utiliza uma abordagem dupla que combina **Recuperação de Informação** (com Modelo Vetorial e TF-IDF) e **Crowdsourcing** para a validação de URLs suspeitas.

## Arquitetura

A arquitetura é composta por dois componentes principais:
1.  **API Backend**: Desenvolvida em Python com FastAPI, responsável pela análise de conteúdo (motor vetorial TF-IDF) e gerenciamento da reputação de URLs (via Firestore).
2.  **Extensão para Google Chrome**: Atua como cliente (compatível com Manifest V3), analisando as páginas visitadas. Ela fornece feedback visual em tempo real através de um **Popup interativo** guiado por estados (seguro, suspeito, perigoso) e alerta o usuário oferecendo ações seguras. A interface também permite que o usuário reporte sites, alimentando diretamente a base de **Crowdsourcing**.

## Autoria

*   **Autores:** [Pedro Henrique Gomes Lückeroth](https://github.com/pedroluckeroth) e [Lucas dos Santos Lima](https://github.com/stllucas).
*   **Orientadora:** [Prof. Dr. Sinaide Nunes Bezerra](https://github.com/sinaide).

## Começando

Estas instruções permitirão que você tenha uma cópia do projeto em execução em sua máquina local para fins de desenvolvimento e teste.

### Pré-requisitos

*   Python 3.10 ou superior
*   Windows ou Linux (para usar os scripts de setup automáticos)

### Instalação Automatizada

Para facilitar a configuração do ambiente, o projeto inclui scripts de automação para Windows e Linux localizados na raiz do repositório (`setup.bat` e `setup.bash`).

Estes scripts cuidam de todo o processo de configuração inicial para você. Eles irão:

1.  Criar um ambiente virtual Python (`venv`) para isolar as dependências.
2.  Ativar o ambiente virtual.
3.  Atualizar o `pip`, o gerenciador de pacotes do Python.
4.  Instalar todas as dependências necessárias para o backend (FastAPI, Uvicorn, NLTK, banco de dados, etc.).
5.  Baixar os dados linguísticos necessários para o NLTK.
6.  Verificar e migrar os índices de dados para um formato otimizado (Tiered Storage / SQLite), caso necessário.

**Como usar:**

*   **No Windows:** Dê um duplo-clique no arquivo `setup.bat` na raiz do projeto ou execute-o através do seu terminal (`.\setup.bat`).
*   **No Linux:** Abra o terminal na raiz do projeto, dê permissão de execução com `chmod +x setup.bash` e execute-o (`./setup.bash`).

Ao final da execução, o script exibirá as instruções para iniciar o servidor da API e carregar a extensão no Chrome.

### Desenvolvimento Local

Se você for atuar como desenvolvedor e estiver rodando a API na sua própria máquina, é necessário ajustar a rota de comunicação na extensão. 

Para isso, abra o arquivo `extension/background.js` e altere o valor da constante `API_ENDPOINT` para a sua rota local (geralmente `http://localhost:8000` ou `http://127.0.0.1:8000`).
