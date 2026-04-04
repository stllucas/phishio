# Relatório de Atualizações Arquiteturais - Front-end Phishio

**Data:** 03 de abril de 2026
**Autor:** Gemini Code Assist

## 1. Visão Geral

Este documento detalha a implementação da nova interface de usuário (UI) para a extensão Phishio, materializada nos arquivos `popup.html`, `popup.css` e `popup.js`. Esta atualização representa um avanço significativo no desenvolvimento do "Módulo Cliente", conforme descrito na Seção 3.1 do TCC. A nova UI é dinâmica, baseada em estados e projetada para fornecer feedback claro e acionável ao usuário, estabelecendo a base para a funcionalidade de crowdsourcing.

## 2. Alinhamento com o Padrão Manifest V3

A arquitetura do front-end foi desenvolvida em estrita conformidade com as políticas de segurança do Manifest V3, um ponto fundamental abordado na Seção 4.1 do TCC.

A implementação segue o princípio da separação de responsabilidades:

*   **Estrutura e Estilo (`popup.html`, `popup.css`):** A interface é definida de forma declarativa, contendo apenas a estrutura visual e os estilos. Não há lógica de script inline, atendendo à política de segurança de conteúdo (CSP) mais restritiva do Manifest V3, que proíbe a execução de códigos não contidos no pacote da extensão.
*   **Lógica de Eventos (`popup.js`):** Toda a interatividade é encapsulada neste arquivo. Ele é responsável por manipular o DOM, adicionar `event listeners` aos botões e, futuramente, comunicar-se com o `service worker` (`background.js`) para obter o estado da página e enviar os reportes do usuário.

Essa separação rigorosa garante que a extensão seja mais segura, performática e fácil de manter, alinhando-se diretamente aos requisitos de "Segurança e Privacidade" e ao uso de `Service Workers` citados no TCC.

## 3. Heurísticas de Nielsen na Prática

Conforme fundamentado na Seção 2.3 ("Crowdsourcing e Usabilidade na Segurança") e na Seção 4.2 do TCC, a interface foi projetada seguindo as heurísticas de usabilidade de Nielsen para garantir que o feedback seja imediato e o esforço cognitivo do usuário seja mínimo.

*   **Visibilidade do Status do Sistema:** A implementação dos 5 painéis dinâmicos (`panel-inactive`, `panel-safe`, `panel-suspicious`, `panel-danger`, `panel-feedback`) é a materialização direta desta heurística. O usuário é informado sobre o estado da análise da página atual de forma inequívoca. O uso semântico de cores (verde para seguro, amarelo para suspeito, vermelho para perigoso) e de ícones (`shield-safe.svg`, etc.) reforça visualmente essa comunicação, tornando o status compreensível em segundos.

*   **Prevenção de Erros e Recuperação:** O painel de perigo (`panel-danger`) é um exemplo claro de prevenção de erros. O botão principal, "Voltar", é destacado em vermelho para incentivar a ação mais segura. Em contraste, a opção de risco, "Ignorar e continuar", é um link discreto, desencorajando o clique acidental. Isso guia o usuário para longe do perigo.

*   **Clareza e Minimalismo:** Cada painel exibe apenas as informações e ações relevantes para aquele contexto específico. Os textos são diretos e claros (ex: "Este site parece seguro", "CUIDADO! PHISHING DETECTADO."), evitando jargões técnicos e garantindo que o alerta seja compreendido por todos os usuários, conforme preconiza Nielsen.

## 4. A Base para o Crowdsourcing

A nova interface é o alicerce para o "Módulo de Crowdsourcing (Feedback)", um dos pilares da abordagem híbrida do Phishio, detalhado nas Seções 3.1 e 4.2 do TCC.

*   **Mecanismo de "Um Clique":** Os botões de reporte (`Reportar site suspeito`, `Reportar como SITE FALSO`, etc.) implementam o mecanismo de "um clique" para a coleta de feedback, exigindo esforço mínimo do usuário, como teorizado na Seção 2.3.

*   **Preparação para o "Human-in-the-Loop":** O arquivo `popup.js` já contém os `event listeners` para cada um desses botões. Esta estrutura está pronta para ser conectada à lógica de comunicação com a API. Ao clicar, o `popup.js` irá obter a URL da aba ativa e enviar o voto do usuário (natureza do voto: -1 para seguro, 1 para phishing) para o endpoint de crowdsourcing no backend.

*   **Integração com o Firestore:** Essa ação do usuário, capturada pela UI, é o ponto de partida do fluxo de crowdsourcing que culmina na atualização do banco de dados colaborativo no Google Firestore. A interface, portanto, habilita o ciclo de feedback contínuo que refina a acurácia do sistema em tempo real, mitigando falsos positivos e negativos.
