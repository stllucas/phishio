const API_ENDPOINT = "https://phishio.duckdns.org";

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "analisarPagina") {
    chrome.storage.local.get(["protectionActive"], function (result) {
      // Se não for explicitamente falso, assumimos que está ligado
      if (result.protectionActive !== false) {
        processarAnalise(request.dados, sender.tab.id);
      } else {
        limparBadge(sender.tab.id);
      }
    });
  }

  if (request.action === "reportUrl") {
    enviarReporteParaAPI(request.url, request.vote).then((sucesso) => {
      if (sucesso) {
        chrome.storage.local.get(["totalAvaliacoes"], (res) => {
          let total = res.totalAvaliacoes || 0;
          chrome.storage.local.set({ totalAvaliacoes: total + 1 });
        });
      }
      sendResponse({ success: sucesso });
    });
    return true;
  }
});

async function processarAnalise(dados, tabId) {
  try {
    const response = await fetch(`${API_ENDPOINT}/check_url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: dados.url,
        content: dados.content,
        dom: dados.dom,
      }),
    });

    if (response.ok) {
      const resultado = await response.json();
      const status = resultado.status;

      // Salva o status exato atrelado à aba específica para o popup ler
      await chrome.storage.local.set({ [`status_${tabId}`]: status });
      atualizarInterface(status, tabId);
    }
  } catch (error) {
    console.error("Erro no motor Phishio:", error);
  }
}

async function enviarReporteParaAPI(url, vote) {
  try {
    const response = await fetch(`${API_ENDPOINT}/reportar_url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url, voto: vote }),
    });
    return response.ok;
  } catch (error) {
    return false;
  }
}

function atualizarInterface(status, tabId) {
  let iconPath = "icons/shield-inactive-48.png";
  let badgeText = "";
  let badgeColor = "#757575";

  if (status === "phishing") {
    iconPath = "icons/shield-danger-48.png";
    badgeText = "X";
    badgeColor = "#F04646";
  } else if (status === "suspect" || status === "suspicious") {
    iconPath = "icons/shield-warning-48.png";
    badgeText = "!";
    badgeColor = "#F7E96D";
  } else if (status === "safe" || status === "secure") {
    iconPath = "icons/shield-safe-48.png";
  }

  chrome.action.setIcon({ tabId: tabId, path: iconPath });
  chrome.action.setBadgeText({ tabId: tabId, text: badgeText });
  chrome.action.setBadgeBackgroundColor({ tabId: tabId, color: badgeColor });
}

function limparBadge(tabId) {
  chrome.action.setBadgeText({ tabId: tabId, text: "" });
  chrome.action.setIcon({ tabId: tabId, path: "icons/shield-inactive-48.png" });
}
