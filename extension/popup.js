/** Script responsável pela lógica de interface e interação do usuário no popup da extensão. */
document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.getElementById("protection-toggle");
  const mainIcon = document.getElementById("main-icon");
  const statusBadge = document.getElementById("status-badge");
  const infoBox = document.getElementById("info-box");
  const boxTitle = document.getElementById("box-title");
  const innerContent = document.getElementById("inner-content");

  function updateDisplayState() {
    chrome.storage.local.get(["protectionActive"], function (result) {
      if (result.protectionActive === false) {
        toggle.checked = false;
        showOffScreen();
      } else {
        toggle.checked = true;
        chrome.tabs.query(
          { active: true, currentWindow: true },
          function (tabs) {
            if (tabs[0]) {
              const tabId = tabs[0].id;
              chrome.storage.local.get([`status_${tabId}`], function (data) {
                const status = data[`status_${tabId}`] || "safe";

                if (status === "phishing") showPerigoScreen();
                else if (status === "suspect" || status === "suspicious")
                  showSuspeitoScreen();
                else showSecureScreen();
              });
            }
          },
        );
      }
    });
  }

function realizarReporte(voto, botaoClicado) {
  chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
    const urlAtual = tabs[0].url;
    const storageKey = `voted_${btoa(urlAtual)}`;

    chrome.storage.local.get([storageKey], (res) => {
      if (res[storageKey]) {
        const container = botaoClicado.parentNode.parentNode;
        const aviso = document.createElement("div");
        aviso.style.color = "#2e7d32";
        aviso.style.fontSize = "12px";
        aviso.style.marginTop = "10px";
        aviso.style.fontWeight = "bold";
        aviso.style.textAlign = "center";
        aviso.textContent = "✔ Você já reportou este site. Estamos computando sua opinião!";
        
        container.appendChild(aviso);
        botaoClicado.disabled = true;
        return;
      }

      const textoOriginal = botaoClicado.innerHTML;
      botaoClicado.innerHTML = "<strong>Enviando...</strong>";
      botaoClicado.disabled = true;

      const erroAntigo = document.getElementById("phishio-inline-error");
      if (erroAntigo) erroAntigo.remove();

      chrome.runtime.sendMessage(
        { action: "reportUrl", url: urlAtual, vote: voto },
        (response) => {
          if (response && response.success) {
            chrome.storage.local.set({ [storageKey]: true });
            showSuccessMessage(voto === 1 ? "fake" : "secure");
          } else {
            botaoClicado.innerHTML = textoOriginal;
            botaoClicado.disabled = false;

            const erroDiv = document.createElement("div");
            erroDiv.id = "phishio-inline-error";
            erroDiv.style.color = "#c62828";
            erroDiv.style.fontSize = "12px";
            erroDiv.style.marginTop = "12px";
            erroDiv.style.fontWeight = "bold";
            erroDiv.style.textAlign = "center";
            erroDiv.style.width = "100%";
            erroDiv.innerHTML = "❌ Erro ao enviar reporte. Tente novamente.";

            botaoClicado.parentNode.parentNode.appendChild(erroDiv);
          }
        }
      );
    });
  });
}
  function atualizarContadorUI() {
    chrome.storage.local.get(["totalAvaliacoes"], (result) => {
      const counts = document.querySelectorAll("#eval-count");
      counts.forEach((el) => (el.textContent = result.totalAvaliacoes || 0));
    });
  }

  updateDisplayState();

  function showOffScreen() {
    removeBackButton();
    mainIcon.src = "images/svg/shield-inactive-128.svg";
    statusBadge.textContent = "Proteção Phishio Desligada";
    statusBadge.className = "status-badge off";
    infoBox.className = "contribution-box off";
    boxTitle.style.display = "none";
    innerContent.innerHTML = `
    <div class="contribution-content">
        <img src="images/svg/thumbsup.png" alt="Joinha" class="thumbsup-icon"> 
        <p style="margin: 0; font-size: 16px; color: #9c6363;">
            Você ajudou a avaliar <span id="eval-count">0</span> 
            <br>sites na nossa rede colaborativa
        </p>
    </div>
`;
    atualizarContadorUI();
  }

  function showSecureScreen() {
    removeBackButton();
    mainIcon.src = "images/svg/shield-active-128.svg";
    statusBadge.textContent = "Este site parece seguro";
    statusBadge.className = "status-badge secure";
    infoBox.className = "contribution-box secure";
    boxTitle.style.display = "none";
    innerContent.innerHTML = `
        <div class="contribution-content">
            <div style="color: #000000; font-weight: 500; margin-bottom: 8px;">
                Análise concluída<br><strong>Sem ameaças detectadas.</strong>
            </div>
            <button class="report-btn" id="go-to-feedback">Reportar site suspeito</button>
        </div>
    `;
    document.getElementById("go-to-feedback").onclick = () => showFeedbackScreen(showSecureScreen);
  }

  function showSuspeitoScreen() {
    removeBackButton();
    mainIcon.src = "images/svg/shield-suspicious-128.svg";
    statusBadge.textContent = "Tenha cautela, este site pode ser perigoso.";
    statusBadge.className = "status-badge suspect";
    infoBox.className = "contribution-box suspect";
    boxTitle.style.display = "none";
    innerContent.innerHTML = `
        <div class="suspect-text">Alguns usuários reportaram<br>este site como suspeito</div>
        <div class="suspect-button-group">
            <button class="suspect-choice-btn btn-choice-secure" id="confirm-secure-choice">Reportar<br>site seguro</button>
            <button class="suspect-choice-btn btn-choice-suspect" id="confirm-suspect-choice">Reportar site<br>suspeito</button>
        </div>
    `;
    document.getElementById("confirm-secure-choice").onclick = (e) =>
      realizarReporte(-1, e.currentTarget);
    document.getElementById("confirm-suspect-choice").onclick = (e) =>
      realizarReporte(1, e.currentTarget);
  }

  function showPerigoScreen() {
    removeBackButton();
    mainIcon.src = "images/svg/shield-danger-128.svg";
    statusBadge.innerHTML = "CUIDADO!<br>PHISHING DETECTADO.";
    statusBadge.className = "status-badge danger";
    infoBox.className = "contribution-box danger";
    boxTitle.style.display = "none";

    innerContent.innerHTML = `
        <div class="danger-text">Identificamos esta<br>página como fraudulenta!</div>
        <div class="danger-button-group">
            <button class="btn-danger-back" id="danger-back-btn"><strong>Voltar</strong></button>
            <button class="btn-danger-ignore" id="danger-ignore-btn">Ignorar<br>(não recomendado)</button>
        </div>
        <a href="#" id="false-positive-link" style="margin-top: 15px; font-size: 11px; color: #555; text-decoration: underline;">
            Reportar como classificação incorreta
        </a>
    `;

    document.getElementById("danger-back-btn").onclick = () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0].id) {
            chrome.tabs.goBack(tabs[0].id);
            window.close();
        }
    });
};
    
    document.getElementById("danger-ignore-btn").onclick = () => window.close();

    document.getElementById("false-positive-link").onclick = (e) => {
    e.preventDefault();
    showFeedbackScreen(showPerigoScreen);
    };
}

  function showFeedbackScreen(voltarPara) {
    addBackButton();
    mainIcon.src = "images/svg/shield-feedback-128.svg";
    statusBadge.textContent = "Encontrou um erro?";
    statusBadge.className = "status-badge feedback";
    infoBox.className = "contribution-box feedback";

    innerContent.innerHTML = `
        <div class="contribution-content">
            <div style="color: #000000; margin-bottom: 5px; font-size: 12px; font-weight: 500;">
                Ajude a Comunidade. Qual o status correto deste site?
            </div>
            <div class="feedback-button-group">
                <button class="report-choice-btn btn-fake" id="report-fake-btn">Reportar como:<br><strong>SITE FALSO</strong></button>
                <button class="report-choice-btn btn-secure" id="report-secure-btn">Reportar como:<br><strong>SITE SEGURO</strong></button>
            </div>
            <div class="tiny-footer-text">Seu voto é anônimo e ajuda a treinar nosso modelo analítico</div>
        </div>
    `;

    document.getElementById("report-fake-btn").onclick = (e) => realizarReporte(1, e.currentTarget);
    document.getElementById("report-secure-btn").onclick = (e) => realizarReporte(-1, e.currentTarget);

    document.getElementById("btn-back").onclick = voltarPara;
}

  function showSuccessMessage(type) {
    let title =
      type === "fake" || type === "suspect"
        ? "✔ Reporte registrado!"
        : "✔ Confirmação registrada!";
    let message =
      type === "fake" || type === "suspect"
        ? "Obrigado por colaborar. Este site foi marcado em nossa base de dados."
        : "Obrigado por confirmar que este site é seguro.";
    let btnText =
      type === "fake" || type === "suspect" ? "Sair deste site" : "Concluir";

    mainIcon.src = "images/svg/shield-active-128.svg";
    statusBadge.textContent = "Ação Concluída!";
    statusBadge.className = "status-badge secure";
    infoBox.className = "contribution-box secure";
    boxTitle.style.display = "none";

    innerContent.innerHTML = `
        <div class="contribution-content" style="min-height: 100px;">
            <div style="color: #2e7d32; font-size: 15px; font-weight: bold; margin-bottom: 10px;">${title}</div>
            <div style="color: #000000; font-size: 13px; line-height: 1.4;">${message}</div>
            <button class="report-btn" style="background-color: ${type === "fake" || type === "suspect" ? "#f04646" : "#d9d9d9"}; color: ${type === "fake" || type === "suspect" ? "#ffffff" : "#000000"}; margin-top: 15px;" id="success-action-btn">
                ${btnText}
            </button>
        </div>
    `;

    document.getElementById("success-action-btn").onclick = () => {
    if (type === "fake" || type === "suspect") {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.tabs.goBack(tabs[0].id);
            window.close();
        });
    } else {
        showSecureScreen();
    }
};
    atualizarContadorUI();
  }

  function addBackButton() {
    if (!document.getElementById("btn-back")) {
      const btn = document.createElement("button");
      btn.id = "btn-back";
      btn.className = "back-button";
      btn.innerHTML = "←";
      btn.onclick = showSecureScreen;
      document.getElementById("content-area").prepend(btn);
    }
  }

  function removeBackButton() {
    const btn = document.getElementById("btn-back");
    if (btn) btn.remove();
  }

  toggle.addEventListener("change", function () {
    const isActive = this.checked;
    
    chrome.storage.local.set({ protectionActive: isActive }, () => {
      chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
        if (tabs[0]) {
          const tabId = tabs[0].id;
          
          if (!isActive) {
            chrome.action.setBadgeText({ tabId: tabId, text: "" });
            chrome.action.setIcon({ tabId: tabId, path: "images/shield-inactive-48.png" });
          } else {
            chrome.tabs.reload(tabId);
          }
        }
      });
      updateDisplayState();
    });
  });
});
