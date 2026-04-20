// --- Listener de Mensagens do Service Worker (background.js) ---
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "getDomContent") {
    const domContent = document.body.innerText;
    sendResponse({ dom: domContent });
    return true;
  }

  if (message.action === "displayPhishingOverlay") {
    if (!document.getElementById("phishio-modal-host")) {
      injectModal(message.status, message.url);
    }
  }
});

/**
 * Cria e injeta o modal com Shadow DOM, Blur e Animações.
 */
function injectModal(status, url) {
  const host = document.createElement("div");
  host.id = "phishio-modal-host";
  document.body.appendChild(host);

  const shadow = host.attachShadow({ mode: "open" });

  // Injeção do HTML e CSS combinados para garantir as animações
  const root = document.createElement("div");
  root.innerHTML = `
        <style>
            /* Overlay com Blur Progressivo */
            .phishio-overlay {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0, 0, 0, 0.4);
                backdrop-filter: blur(8px);
                -webkit-backdrop-filter: blur(8px);
                z-index: 999999999;
                display: flex; align-items: center; justify-content: center;
                opacity: 0;
                animation: phishioFadeIn 0.4s ease forwards;
                font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }

            /* Caixa do Modal com Movimento Suave */
            .phishio-modal {
                background: white;
                border-radius: 16px;
                width: 400px;
                text-align: center;
                box-shadow: 0 20px 50px rgba(0,0,0,0.3);
                overflow: hidden;
                transform: translateY(30px) scale(0.95);
                opacity: 0;
                animation: phishioSlideUp 0.5s cubic-bezier(0.17, 0.89, 0.32, 1.28) 0.1s forwards;
            }

            .phishio-header {
                padding: 25px;
                color: white;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 15px;
            }

            /* Cores baseadas no status */
            .phishio-header--phishing { background: #c9302c; }
            .phishio-header--suspicious { background: #f0ad4e; }

            .phishio-icon { width: 64px; height: 64px; }
            
            .phishio-body { padding: 30px; }
            
            .phishio-title { margin: 0; font-size: 20px; font-weight: bold; }
            
            .phishio-message { color: #555; line-height: 1.5; margin: 15px 0 25px 0; font-size: 15px; }

            .phishio-btn-primary {
                background: #333; color: white; border: none;
                padding: 14px 25px; border-radius: 8px; cursor: pointer;
                font-size: 16px; font-weight: bold; width: 100%;
                transition: background 0.2s;
            }
            .phishio-header--phishing + .phishio-body .phishio-btn-primary { background: #c9302c; }
            .phishio-header--suspicious + .phishio-body .phishio-btn-primary { background: #f0ad4e; }

            .phishio-btn-primary:hover { filter: brightness(90%); }

            .phishio-footer { margin-top: 20px; border-top: 1px solid #eee; padding-top: 20px; }

            .phishio-link { color: #888; text-decoration: none; font-size: 13px; cursor: pointer; }
            .phishio-link:hover { text-decoration: underline; }

            .phishio-feedback { font-size: 12px; color: #5cb85c; margin-top: 10px; }

            @keyframes phishioFadeIn { to { opacity: 1; } }
            @keyframes phishioSlideUp { 
                to { transform: translateY(0) scale(1); opacity: 1; } 
            }
        </style>
        ${getModalHtml(status, url)}
    `;

  shadow.appendChild(root);
  addModalEventListeners(shadow, url, host);
}

function addModalEventListeners(shadow, url, host) {
  // 1. Botão Voltar
  const backButton = shadow.getElementById("phishio-back-btn");
  if (backButton) {
    backButton.onclick = () => {
      if (window.history.length > 1) {
        window.history.back();
      } else if (document.referrer) {
        window.location.href = document.referrer;
      } else {
        window.location.href = "https://www.google.com";
      }
    };
  }

  // 2. Botão Ignorar
  const ignoreButton = shadow.getElementById("phishio-ignore-btn");
  if (ignoreButton) {
    ignoreButton.onclick = (e) => {
      e.preventDefault();
      host.remove();
    };
  }

  // 3. Botão Reportar como Seguro
  const reportSafeButton = shadow.getElementById("phishio-report-safe-btn");
  if (reportSafeButton) {
    reportSafeButton.onclick = (e) => {
      e.preventDefault();
      // Chama a função reportUrl com voto -1 (Seguro)
      reportUrl(url, -1, shadow, host);
    };
  }
}

function reportUrl(url, vote, shadow, host) {
  const feedback = shadow.getElementById("phishio-feedback-text");
  feedback.textContent = "Enviando reporte...";

  chrome.runtime.sendMessage(
    { action: "reportUrl", url: url, vote: vote },
    (response) => {
      if (response && response.success) {
        feedback.textContent = "Obrigado! Reporte registrado.";
        setTimeout(() => host.remove(), 2000);
      } else {
        feedback.textContent = "Erro ao enviar reporte.";
      }
    },
  );
}

function getModalHtml(status, url) {
  const urlHost = new URL(url).hostname;
  const isPhishing = status === "phishing";

  const config = {
    icon: chrome.runtime.getURL(
      isPhishing
        ? "icons/shield-danger-128.png"
        : "icons/shield-warning-128.png",
    ),
    headerClass: isPhishing
      ? "phishio-header--phishing"
      : "phishio-header--suspicious",
    title: isPhishing ? "CUIDADO! SITE PERIGOSO" : "ATENÇÃO! SITE SUSPEITO",
    message: isPhishing
      ? `O Phishio identificou que <strong>${urlHost}</strong> é um site de phishing criado para roubar seus dados.`
      : `O site <strong>${urlHost}</strong> possui comportamento suspeito. Evite inserir senhas ou dados pessoais.`,
    btnText: isPhishing ? "Sair agora (Recomendado)" : "Voltar",
  };

  return `
        <div class="phishio-overlay">
            <div class="phishio-modal">
                <div class="phishio-header ${config.headerClass}">
                    <img src="${config.icon}" class="phishio-icon">
                    <h1 class="phishio-title">${config.title}</h1>
                </div>
                <div class="phishio-body">
                    <p class="phishio-message">${config.message}</p>
                    <button id="phishio-back-btn" class="phishio-btn-primary">${config.btnText}</button>
                    
                    <div class="phishio-footer">
                        <a id="phishio-ignore-btn" class="phishio-link">Ignorar aviso e continuar</a>
                        <br><br>
                        <span style="font-size:12px; color:#aaa">Acha que é um erro? 
                            <a id="phishio-report-safe-btn" class="phishio-link" style="text-decoration:underline">Reportar como seguro</a>
                        </span>
                        <p id="phishio-feedback-text" class="phishio-feedback"></p>
                    </div>
                </div>
            </div>
        </div>
    `;
}
