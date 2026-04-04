document.addEventListener('DOMContentLoaded', () => {
    // Get all panel elements
    const API_ENDPOINT = 'http://127.0.0.1:8000/check_url'; // For consistency, though not used directly here
    const REPORT_ENDPOINT = 'http://127.0.0.1:8000/reportar_url';
    const panels = document.querySelectorAll('.panel');
    
    // Get all button elements that need listeners
    const btnReportSuspiciousFromSafe = document.getElementById('report-suspicious-from-safe');
    const btnReportSafeFromSuspicious = document.getElementById('report-safe-from-suspicious');
    const btnReportSuspiciousFromSuspicious = document.getElementById('report-suspicious-from-suspicious');
    const btnGoBack = document.getElementById('go-back');
    const btnIgnoreWarning = document.getElementById('ignore-warning');
    const btnReportFake = document.getElementById('report-fake');
    const btnReportSafeFromFeedback = document.getElementById('report-safe-from-feedback');
    const protectionToggle = document.getElementById('protection-toggle');
    const statusText = document.getElementById('protection-status-text');

    /**
     * Hides all panels and shows the one with the specified ID.
     * @param {string} panelId The ID of the panel to show.
     */
    function showPanel(panelId) {
        panels.forEach(panel => {
            if (panel.id === panelId) {
                panel.style.display = 'flex'; // Use flex to enable vertical centering
            } else {
                panel.style.display = 'none';
            }
        });
    }

    /**
     * Sends a URL report to the backend.
     * @param {string} url The URL to be reported.
     * @param {number} vote The user's vote (1 for phishing, -1 for safe).
     */
    async function sendReport(url, vote) {
        try {
            const response = await fetch(REPORT_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url, voto: vote }),
            });
            const result = await response.json();
            console.log('Report sent:', result);
            // Update the status in local storage after the report.
            await chrome.storage.local.set({ [url]: result.new_status });
            alert(`Reporte recebido! Novo status: ${result.new_status}.`);
            window.close(); // Close the popup after the report.
        } catch (error) {
            console.error('Error sending report:', error);
            alert('Erro ao enviar reporte. Tente novamente.');
        }
    }

    // --- Event Listeners (with placeholder logic) ---

    if (btnReportSuspiciousFromSafe) {
        btnReportSuspiciousFromSafe.addEventListener('click', async () => {
            console.log('Action: Report site as suspicious (from safe panel)');
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tab && tab.url) {
                await sendReport(tab.url, 1); // Report as phishing
            }
        });
    }

    if (btnReportSafeFromSuspicious) {
        btnReportSafeFromSuspicious.addEventListener('click', async () => {
            console.log('Action: Report site as safe (from suspicious panel)');
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tab && tab.url) {
                await sendReport(tab.url, -1); // Report as safe
            }
        });
    }

    if (btnReportSuspiciousFromSuspicious) {
        btnReportSuspiciousFromSuspicious.addEventListener('click', async () => {
            console.log('Action: Report site as suspicious (from suspicious panel)');
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tab && tab.url) {
                await sendReport(tab.url, 1); // Report as phishing
            }
        });
    }

    if (btnGoBack) {
        btnGoBack.addEventListener('click', async () => {
            console.log('Action: Go back (from danger panel)');
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tab && tab.id) {
                chrome.tabs.goBack(tab.id);
                window.close();
            }
        });
    }

    if (btnIgnoreWarning) {
        btnIgnoreWarning.addEventListener('click', () => {
            console.log('Action: Ignore warning and continue (from danger panel)');
            window.close();
        });
    }

    if (btnReportFake) {
        btnReportFake.addEventListener('click', async () => {
            console.log('Action: Report as FAKE site (from feedback panel)');
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tab && tab.url) {
                await sendReport(tab.url, 1); // Report as phishing
            }
        });
    }

    if (btnReportSafeFromFeedback) {
        btnReportSafeFromFeedback.addEventListener('click', async () => {
            console.log('Action: Report as SAFE site (from feedback panel)');
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tab && tab.url) {
                await sendReport(tab.url, -1); // Reportar como seguro
            }
        });
    }

async function initializePanels() {
    try {
        // 1. Primeiro, pegamos a aba ativa corretamente
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        // 2. Verifica se a proteção global está ativa
        const storage = await chrome.storage.local.get(['protectionStatus']);
        const isEnabled = storage.protectionStatus !== false;

        if (!isEnabled) {
            showPanel('panel-inactive');
            updateProtectionStatus(false);
            return; 
        }

        // 3. Se estiver ativa, verificamos o status desta URL específica
        if (tab && tab.url) {
            const url = tab.url;
            const result = await chrome.storage.local.get(url);
            const status = result[url];

            console.log(`Phishio Debug: URL=${url}, Status=${status}`);

            // Mapeamento de status para painéis
            if (status === 'safe' || status === 'seguro') {
                showPanel('panel-safe');
            } else if (status === 'warning' || status === 'suspicious' || status === 'suspeito') {
                showPanel('panel-suspicious');
            } else if (status === 'danger' || status === 'phishing' || status === 'perigoso') {
                showPanel('panel-danger');
            } else {
                // Se a proteção está ligada mas não temos veredito, 
                // mostramos o painel "Safe" (ou você pode criar um painel "Analisando...")
                showPanel('panel-safe'); 
            }
        } else {
            showPanel('panel-inactive');
        }
    } catch (error) {
        console.error("Erro ao inicializar painéis:", error);
    }
}

    // --- Lógica do Toggle de Proteção ---
    function updateProtectionStatus(isEnabled) {
        statusText.textContent = isEnabled ? 'Proteção Ativa' : 'Proteção Desligada';
    }

    if (protectionToggle) {
        // Listener para quando o usuário altera o toggle
        protectionToggle.addEventListener('change', (event) => {
            const isEnabled = event.target.checked;
            chrome.storage.local.set({ protectionStatus: isEnabled }, () => {
                console.log(`Phishio: Estado da proteção salvo como ${isEnabled}`);
                updateProtectionStatus(isEnabled);
                initializePanels();
            });
        });

        // Inicializa o estado do toggle ao abrir o popup
        chrome.storage.local.get(['protectionStatus'], (result) => {
            const isEnabled = result.protectionStatus !== false; // Ativado por padrão se não definido
            protectionToggle.checked = isEnabled;
            updateProtectionStatus(isEnabled);
        });
    }

    initializePanels();
});
