// popup.js
document.addEventListener("DOMContentLoaded", () => {
  const panels = document.querySelectorAll(".panel");
  const protectionToggle = document.getElementById("protection-toggle");
  const statusText = document.getElementById("protection-status-text");

  function showPanel(panelId) {
    panels.forEach((panel) => {
      panel.style.display = panel.id === panelId ? "flex" : "none";
    });
  }

  // Centralizado: Envia mensagem para o background.js em vez de fazer fetch
  async function sendReport(url, vote) {
    chrome.runtime.sendMessage(
      { action: "reportUrl", url: url, vote: vote },
      async (response) => {
        if (response && response.success) {
          const result = response.data;
          // Padronização: 'new_status' deve vir como 'safe', 'suspicious' ou 'phishing'
          await chrome.storage.local.set({ [url]: result.new_status });
          alert(
            `Obrigado! O status foi atualizado para: ${result.new_status}.`,
          );
          initializePanels();
        } else {
          alert("Erro ao enviar reporte através do Service Worker.");
        }
      },
    );
  }

  async function initializePanels() {
    try {
      const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true,
      });
      const storage = await chrome.storage.local.get(["protectionStatus"]);
      const isEnabled = storage.protectionStatus !== false;

      if (!isEnabled || !tab || !tab.url) {
        showPanel("panel-inactive");
        updateProtectionStatus(false);
        return;
      }

      const result = await chrome.storage.local.get(tab.url);
      const status = result[tab.url];

      // Padronização de strings para evitar redundância (Safe/Suspicious/Phishing)
      if (status === "safe") {
        showPanel("panel-safe");
      } else if (status === "suspicious") {
        showPanel("panel-suspicious");
      } else if (status === "phishing") {
        showPanel("panel-danger");
      } else {
        showPanel("panel-safe");
      }
    } catch (error) {
      console.error("Erro ao inicializar painéis:", error);
    }
  }

  // Listeners dos botões (Exemplos)
  document
    .getElementById("report-safe-from-feedback")
    ?.addEventListener("click", async () => {
      const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true,
      });
      if (tab?.url) await sendReport(tab.url, -1);
    });

  document
    .getElementById("report-fake")
    ?.addEventListener("click", async () => {
      const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true,
      });
      if (tab?.url) await sendReport(tab.url, 1);
    });

  function updateProtectionStatus(isEnabled) {
    statusText.textContent = isEnabled
      ? "Proteção Ativa"
      : "Proteção Desligada";
  }

  if (protectionToggle) {
    protectionToggle.addEventListener("change", (event) => {
      const isEnabled = event.target.checked;
      chrome.storage.local.set({ protectionStatus: isEnabled }, () => {
        updateProtectionStatus(isEnabled);
        initializePanels();
      });
    });

    chrome.storage.local.get(["protectionStatus"], (result) => {
      const isEnabled = result.protectionStatus !== false;
      protectionToggle.checked = isEnabled;
      updateProtectionStatus(isEnabled);
    });
  }

  initializePanels();
});
