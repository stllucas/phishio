# O phishio

**Phishio** é um sistema híbrido para detecção de *phishing* em tempo real, desenvolvido como um **Trabalho de Conclusão de Curso (TCC)**.

O projeto utiliza uma abordagem dupla que combina **Recuperação de Informação** (com Modelo Vetorial e TF-IDF) e **Crowdsourcing** para a validação de URLs suspeitas.

## Arquitetura

A arquitetura é composta por dois componentes principais:
1.  **API Backend**: Desenvolvida em Python com FastAPI, responsável pela análise de conteúdo (motor vetorial TF-IDF) e gerenciamento da reputação de URLs (via Firestore).
2.  **Extensão para Google Chrome**: Atua como cliente, analisando as páginas que o usuário visita. Em caso de detecção de ameaça, a extensão **injeta uma tela de bloqueio (overlay)** diretamente na página, alertando o usuário e oferecendo ações seguras, como voltar para a página anterior.

## Autoria

*   **Autores:** [Pedro Henrique Gomes Lückeroth](https://github.com/pedroluckeroth) e [Lucas dos Santos Lima](https://github.com/stllucas).
*   **Orientadora:** [Prof.ª Dr.ª Sinaide Nunes Bezerra](https://github.com/sinaide).

## Começando

Estas instruções permitirão que você tenha uma cópia do projeto em execução em sua máquina local para fins de desenvolvimento e teste.

### Pré-requisitos

*   Python 3.10 ou superior
*   Windows (para usar o script de setup automático)

### Instalação Automatizada (Windows)

Para facilitar a configuração do ambiente de desenvolvimento em máquinas Windows, o projeto inclui um script de automação localizado em `scripts\setup.bat`.

Este script cuida de todo o processo de configuração inicial para você. Ele irá:

1.  Criar um ambiente virtual Python (`venv`) para isolar as dependências.
2.  Ativar o ambiente virtual.
3.  Atualizar o `pip`, o gerenciador de pacotes do Python.
4.  Instalar todas as dependências necessárias para o backend (FastAPI, Uvicorn, NLTK, etc.).
5.  Baixar os dados linguísticos necessários para o NLTK.
6.  Verificar e otimizar os índices de dados para melhor performance.

**Como usar:**

Basta executar o arquivo `setup.bat` localizado na pasta `scripts`. Você pode fazer isso dando um duplo-clique no arquivo ou executando-o através do seu terminal. Ao final da execução, o script exibirá as instruções para iniciar o servidor da API e carregar a extensão no Chrome.
