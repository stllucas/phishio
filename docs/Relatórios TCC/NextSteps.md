# Análise Técnica e Roadmap de Finalização - Projeto Phishio

## 1. Visão Geral

Sua implementação atual da extensão Phishio demonstra um entendimento correto dos fundamentos do Manifest V3. A utilização de um `service_worker` para eventos, a injeção de scripts com a API `scripting` e a definição de `host_permissions` para a comunicação com o backend estão em conformidade com as diretrizes do Google.

A análise a seguir foca em refinar a implementação para que ela corresponda integralmente à metodologia descrita em seu TCC (`versao-mais-atual-tcc-latex-file.tex`) e para garantir que a solução seja robusta, segura e completa para a demonstração.

## 2. Revisão de Segurança e APIs (Manifest V3)

**Ponto Analisado:** A implementação atual do `service_worker` utiliza `declarativeNetRequest` ou métodos de interceptação obsoletos?

**Resposta:** Não, e isso está **correto**.

*   **O método atual é o adequado:** Sua abordagem utiliza o `chrome.tabs.onUpdated` para detectar a conclusão do carregamento de uma página. Isso é ideal para o seu caso de uso, que é a **análise de conteúdo pós-carregamento**.
*   **Por que `declarativeNetRequest` não se aplica:** A API `declarativeNetRequest` é projetada para interceptar e agir sobre requisições de rede *antes* que elas aconteçam (por exemplo, para bloquear um rastreador ou redirecionar uma URL). O Phishio, por outro lado, precisa do conteúdo (DOM) da página para realizar a análise vetorial (TF-IDF), algo que só está disponível *após* a página carregar.
*   **Conclusão de Segurança:** A arquitetura atual é segura e eficiente para o propósito descrito, evitando o uso de APIs que não se encaixam no modelo de análise de conteúdo.

## 3. Alinhamento com a Metodologia do TCC

**Ponto Analisado:** A lógica de detecção no código condiz com a metodologia descrita no documento acadêmico?

**Resposta:** Parcialmente. O código atual implementa uma parte crucial do fluxo, mas omite a lógica híbrida que é o diferencial do seu trabalho.

*   **O que está correto:** O fluxo de extrair o conteúdo da página (`content.js`), enviá-lo para a API (`background.js`) e exibir um alerta de phishing está alinhado com a etapa de "URL Desconhecida (Zero-hora)" descrita na Figura 2 do seu TCC.

*   **Principal Gap de Lógica:** O seu TCC (Figura 2) descreve um fluxo híbrido otimizado:
    1.  Primeiro, a API deve consultar a base de reputação colaborativa (**Firestore**).
    2.  Apenas se a URL for desconhecida, o custoso processamento vetorial (TF-IDF + Cosseno) deve ser acionado.

    A implementação atual no `background.js` envia **todas** as URLs diretamente para a análise completa, o que não reflete a eficiência do modelo híbrido proposto.

*   **Funcionalidade Ausente:** Toda a camada de **Crowdsourcing** (feedback do usuário) mencionada no TCC como um dos três módulos principais ainda não foi implementada no lado do cliente.

## 4. Roadmap de Finalização para a Demonstração

Para que a solução esteja completa e alinhada ao seu TCC, sugiro os seguintes passos de implementação, organizados por módulo:

### Módulo 1: Implementar o Crowdsourcing (Extensão)

O `manifest.json` já aponta para um `popup.html`, que é o local ideal para a interação do usuário.

*   **[ ] Criar `popup.html`:** Desenvolver a interface de usuário (UI) do popup. Ela deve ser simples, contendo botões como "Reportar como Seguro" e "Reportar como Phishing".
*   **[ ] Criar `popup.js`:** Implementar a lógica do popup.
    *   Obter a URL da aba ativa (`chrome.tabs.query`).
    *   Adicionar `event listeners` aos botões.
    *   Ao clicar, enviar o voto do usuário e a URL para um novo endpoint no backend (ex: `POST /api/reportar_url`).
    *   Exibir uma confirmação ao usuário na própria interface do popup.
*   **[ ] Criar Ativos Visuais:** Produzir os ícones de status (`icon48-safe.png`, `icon48-warning.png`, `icon48-danger.png`) para que o `background.js` possa fornecer feedback visual dinâmico na barra de ferramentas.

### Módulo 2: Evoluir a Lógica do Backend (API em Python)

O backend precisa refletir a inteligência híbrida descrita no TCC.

*   **[ ] Refatorar o Endpoint `/check_url`:**
    *   Modificar a lógica para **primeiro** consultar a coleção de reputação no Firestore.
    *   Se um consenso para a URL já existir, retornar o veredito (`seguro` ou `perigoso`) imediatamente, sem acionar o motor vetorial.
    *   **Somente se** a URL não estiver no Firestore, prosseguir com a análise de conteúdo (TF-IDF).
*   **[ ] Criar o Endpoint `/reportar_url`:**
    *   Desenvolver este novo endpoint para receber os votos do `popup.js`.
    *   Implementar a "Lógica de Consenso e Reputação" (Seção 5.3 do TCC), atualizando os contadores de votos e o score de consenso da URL no Firestore.

### Módulo 3: Refinar o Service Worker (`background.js`)

Com o backend aprimorado, o service worker pode fornecer um feedback mais rico.

*   **[ ] Tratar Múltiplos Status:** Modificar o `fetch` no `background.js` para interpretar diferentes respostas da API (ex: `{ "status": "seguro" }`, `{ "status": "suspeito" }`, `{ "status": "perigoso" }`).
*   **[ ] Implementar Alertas Visuais Dinâmicos:** Com base na resposta da API, usar `chrome.action.setIcon()` para alterar o ícone da extensão para a cor correspondente (verde, amarelo, vermelho), como sugerido no seu TCC.

---

Ao concluir estes três módulos, sua solução estará 100% funcional, segura e, mais importante, perfeitamente alinhada com a arquitetura e a metodologia inovadora que você propôs em seu trabalho acadêmico.
