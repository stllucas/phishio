document.addEventListener('DOMContentLoaded', function() {
    const toggle = document.getElementById('protection-toggle');
    const mainIcon = document.getElementById('main-icon');
    const statusBadge = document.getElementById('status-badge');
    const infoBox = document.getElementById('info-box');
    const boxTitle = document.getElementById('box-title');
    const innerContent = document.getElementById('inner-content');
    const container = document.querySelector('.container');

    // sites pra testar
    const sitesSuspeitos = ["github.com", "teste.com"];
    const sitesPerigosos = ["malicioso.com", "phishing.net"];

    // SWITCH TELAS
    function updateDisplayState() {
        chrome.storage.local.get(['protectionActive'], function(result) {
            if (!result.protectionActive) {
                toggle.checked = false;
                showOffScreen();
            } else {
                toggle.checked = true;
                chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
                    if (tabs[0] && tabs[0].url) {
                        try {
                            const url = new URL(tabs[0].url).hostname;

                            if (sitesPerigosos.includes(url)) {
                                showPerigoScreen();
                            } else if (sitesSuspeitos.includes(url)) {
                                showSuspeitoScreen();
                            } else {
                                showSecureScreen();
                            }
                        } catch (e) {
                            showSecureScreen();
                        }
                    }
                });
            }
        });
    }

    // INICIALIZAÇÃO
    updateDisplayState();

    // TELA DESLIGADO 
    function showOffScreen() {
        removeBackButton();
        mainIcon.src = "images/svg/shield-inactive-128.svg";
        statusBadge.textContent = "Proteção Phishio Desligada";
        statusBadge.className = "status-badge off";
        infoBox.className = "contribution-box off";
        boxTitle.style.display = 'none'; 
        innerContent.innerHTML = `
            <div class="contribution-content">
                <p style="margin: 0; font-size: 16px; color: #9c6363;">
                    Você ajudou a avaliar <span id="eval-count">[x]</span> 
                    <img src="images/svg/thumbsup.png" alt="Joinha" class="thumbsup-icon"> 
                    <br>sites na nossa rede colaborativa
                </p>
            </div>
        `;
    }

    //TELA SEGURA 
    function showSecureScreen() {
        removeBackButton();
        mainIcon.src = "images/svg/shield-active-128.svg";
        statusBadge.textContent = "Este site parece seguro";
        statusBadge.className = "status-badge secure"; 
        infoBox.className = "contribution-box secure";
        boxTitle.style.display = 'none';
        innerContent.innerHTML = `
            <div class="contribution-content">
                <div style="color: #000000; font-weight: 500; margin-bottom: 8px;">
                    Análise concluída<br>
                    <strong>Sem ameaças detectadas.</strong>
                </div>
                <button class="report-btn" id="go-to-feedback">Reportar site suspeito</button>
            </div>
        `;
        document.getElementById('go-to-feedback').onclick = showFeedbackScreen;
    }

//TELA SUSPEITA
function showSuspeitoScreen() {
    removeBackButton();

    mainIcon.src = "images/svg/shield-suspicious-128.svg";
    
    statusBadge.textContent = "Tenha cautela, este site pode ser perigoso.";
    statusBadge.className = "status-badge suspect"; 
    
    infoBox.className = "contribution-box suspect";
    boxTitle.style.display = 'none';

    innerContent.innerHTML = `
        <div class="suspect-text">
            Alguns usuários reportaram<br>este site como suspeito
        </div>
        <div class="suspect-button-group">
            <button class="suspect-choice-btn btn-choice-secure" id="confirm-secure-choice">
                Reportar<br>site seguro
            </button>
            <button class="suspect-choice-btn btn-choice-suspect" id="confirm-suspect-choice">
                Reportar site<br>suspeito
            </button>
        </div>
    `;

    document.getElementById('confirm-secure-choice').onclick = () => showSuccessMessage('secure');
    document.getElementById('confirm-suspect-choice').onclick = () => showSuccessMessage('suspect');
}

    // TELA PERIGO 
    function showPerigoScreen() {
    removeBackButton();
    mainIcon.src = "images/svg/shield-danger-128.svg";
    
    //badge
    statusBadge.innerHTML = "CUIDADO!<br>PHISHING DETECTADO.";
    statusBadge.className = "status-badge danger"; 
    
    //alert
    infoBox.className = "contribution-box danger";
    boxTitle.style.display = 'none';

    innerContent.innerHTML = `
        <div class="danger-text">
            Identificamos esta<br>página como fraudulenta!
        </div>
        <div class="danger-button-group">
            <button class="btn-danger-back" id="danger-back-btn">
                <strong>Voltar<strong>
            </button>
            <button class="btn-danger-ignore" id="danger-ignore-btn">
                Ignorar<br><strong>(não recomendado)</strong>
            </button>
        </div>
    `;

    //action
    document.getElementById('danger-back-btn').onclick = () => {
        chrome.tabs.update({ url: "https://www.google.com" }, () => {
            showSecureScreen();
            window.close();
        });
    };

    document.getElementById('danger-ignore-btn').onclick = () => {
        window.close();
    };
}

    // TELA FEEDBACK
    function showFeedbackScreen() {
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
                <div class="button-group">
                    <button class="report-choice-btn btn-fake" id="report-fake-btn">Reportar como<br><strong>SITE FALSO</strong></button>
                    <button class="report-choice-btn btn-secure" id="report-secure-btn">Reportar como<br><strong>SITE SEGURO</strong></button>
                </div>
                <div class="tiny-footer-text">Seu voto é anônimo e ajuda a treinar nosso modelo analítico</div>
            </div>
        `;
        document.getElementById('report-fake-btn').onclick = () => showSuccessMessage('fake');
        document.getElementById('report-secure-btn').onclick = () => showSuccessMessage('secure');
    }

    // func SUCCESS
    function showSuccessMessage(type) {
    let title = "";
    let message = "";
    let btnText = "Concluir";
    let isExitBtn = false;

    if (type === 'fake' || type === 'suspect') {
        title = "✔ Reporte registrado!";
        message = "Obrigado por colaborar. Este site foi marcado em nossa base de dados.";
        btnText = "Sair deste site";
        isExitBtn = true;
    } else {
        title = "✔ Confirmação registrada!";
        message = "Obrigado por confirmar que este site é seguro.";
        btnText = "Concluir";
        isExitBtn = false;
    }

    innerContent.innerHTML = `
        <div class="contribution-content" style="min-height: 100px;">
            <div style="color: #2e7d32; font-size: 15px; font-weight: bold; margin-bottom: 10px;">
                ${title}
            </div>
            <div style="color: #000000; font-size: 13px; line-height: 1.4;">
                ${message}
            </div>
            <button class="report-btn" style="background-color: #d9d9d9; margin-top: 15px;" id="success-action-btn">
                ${btnText}
            </button>
        </div>
    `;

    const actionBtn = document.getElementById('success-action-btn');

    if (isExitBtn) {
    actionBtn.style.backgroundColor = "#f04646";
    actionBtn.style.color = "#ffffff";
    
    actionBtn.onclick = () => {
        chrome.tabs.update({ url: "https://www.google.com" }, () => {
            chrome.action.setBadgeText({ text: "" });
            showSecureScreen();
            window.close();
        });
    };
    } else {
        actionBtn.onclick = showSecureScreen;
        }
    }  

    // NAVEGAÇÃO
    function addBackButton() {
        if (!document.getElementById('btn-back')) {
            const btn = document.createElement('button');
            btn.id = 'btn-back';
            btn.className = 'back-button';
            btn.innerHTML = '←'; 
            btn.onclick = showSecureScreen;
            const mainContent = document.getElementById('content-area');
            mainContent.prepend(btn);
        }
    }

    function removeBackButton() {
        const btn = document.getElementById('btn-back');
        if (btn) btn.remove();
    }

    //TOGGLE LOGIC 
    toggle.addEventListener('change', function() {
    const isActive = this.checked;
    chrome.storage.local.set({ protectionActive: isActive }, () => {
        if (!isActive) {
            chrome.action.setBadgeText({ text: "" });
        }
        updateDisplayState();
    });
});
});