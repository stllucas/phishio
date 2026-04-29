<div align="center">
  <img src="icons/logo-phishio.png" alt="Logo Phishio" width="200" />
  <p><em>Sistema Híbrido Colaborativo para Detecção de Phishing em Tempo Real</em></p>
</div>

---

## Site do Projeto

https://pedroluckeroth.github.io/Site-Phishio-TCC-Extension/

---

## Sobre o Projeto

**Phishio** é um sistema híbrido para detecção de *phishing* em tempo real, desenvolvido como um Trabalho de Conclusão de Curso (TCC). 

O projeto utiliza uma abordagem dupla que combina a precisão da Recuperação de Informação (utilizando o Modelo Vetorial e TF-IDF) com o poder do Crowdsourcing para a validação comunitária de URLs suspeitas.

## Arquitetura

A arquitetura do projeto é composta por dois componentes principais interligados:

* **API Backend:** Desenvolvida em `Python` com o framework `FastAPI`, é responsável pela análise profunda de conteúdo (utilizando motor vetorial TF-IDF) e pelo gerenciamento da reputação das URLs via **Firestore** (Firebase).
* **Extensão para Google Chrome:** Atua como o cliente do sistema (compatível com **Manifest V3**), analisando silenciosamente as páginas visitadas.
* **Feedback Visual:** Fornece retorno em tempo real através de um *Popup* interativo guiado por estados claros (🟢 Seguro, 🟡 Suspeito, 🔴 Perigoso).
* **Interatividade:** Alerta o usuário oferecendo ações seguras para evitar ataques. Além disso, a interface permite que o usuário reporte sites maliciosos facilmente, alimentando diretamente a base de dados de *Crowdsourcing*.

---

## Instalação e Utilização do Phishio

Siga os passos abaixo para instalar e rodar a extensão diretamente no seu navegador Google Chrome:

1. **Obtenha o Pacote:** Baixe o arquivo `.zip` da *Release* mais recente neste repositório e extraia o seu conteúdo para uma pasta de fácil acesso em seu computador.
2. **Habilite o Modo do Desenvolvedor:** * Abra o Google Chrome.
   * Digite `chrome://extensions` na sua barra de endereço e aperte Enter.
   * No canto superior direito da tela, ative a chave **"Modo do desenvolvedor"**.
3. **Carregue a Extensão:** * Clique no botão **"Carregar sem compactação"** (no canto superior esquerdo da tela).
   * Selecione a pasta `extension` (dentro dos arquivos que você acabou de extrair).
   * *Pronto! A proteção já está ativa no seu navegador.*

---

## 👨‍🎓 Autoria

* **Autores:** Pedro Henrique Gomes Lückeroth e Lucas dos Santos Lima
* **Orientadora:** Prof. Sinaide Nunes Bezerra
* **Instituição:** Pontífica Universidade Católica de Minas Gerais