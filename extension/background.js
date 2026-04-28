/** Script de background (Service Worker) responsável por gerenciar a comunicação com a API. */
const API_ENDPOINT = "https://phishio.duckdns.org";

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
 if (request.action === "analisarPagina") {
    chrome.storage.local.get(["protectionActive", "lgpdConsent"], (result) => {
      
      if (!result.lgpdConsent) {
        limparBadge(sender.tab.id);
        sendResponse({ needsContent: false, protectionActive: false });
        return; 
      }

      if (result.protectionActive !== false) {
        verificarRapida(request.url, sender.tab.id, sendResponse);
      } else {
        limparBadge(sender.tab.id);
        sendResponse({ needsContent: false, protectionActive: false });
      }
    });
    return true;
  }

  if (request.action === "enviarDadosCompletos") {
    processarAnaliseCompleta(request.dados, sender.tab.id);
    return true;
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

chrome.tabs.onRemoved.addListener((tabId) => {
  chrome.storage.local.remove(`status_${tabId}`);
});

async function verificarRapida(url, tabId, sendResponse) {
  setAnalizandoStatus(tabId);
  try {
    const response = await fetch(`${API_ENDPOINT}/check_url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const resultado = await response.json();

    if (resultado.status === "needs_content" || resultado.status === "unknown") {
      sendResponse({ needsContent: true, protectionActive: true });
    } else {
      await chrome.storage.local.set({ [`status_${tabId}`]: resultado.status });
      atualizarInterface(resultado.status, tabId);
      sendResponse({ needsContent: false, protectionActive: true });
    }
  } catch (error) {
    console.error("Erro na verificação rápida:", error);
    sendResponse({ needsContent: true, protectionActive: true });
  }
}

async function processarAnaliseCompleta(dados, tabId) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);

  try {
    const response = await fetch(`${API_ENDPOINT}/check_url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    if (response.ok) {
      const resultado = await response.json();
      await chrome.storage.local.set({ [`status_${tabId}`]: resultado.status });
      atualizarInterface(resultado.status, tabId);
    } else {
      console.error(`Falha no envio do DOM. Status HTTP: ${response.status}`);
      const errText = await response.text();
      console.error(`Detalhes: ${errText}`);
    }
  } catch (error) {
    clearTimeout(timeoutId);
    console.error(`Erro na análise (CORS, Payload Size ou Timeout) para ${dados.url}:`, error);
  }
}

function setAnalizandoStatus(tabId) {
  chrome.action.setBadgeBackgroundColor({ tabId: tabId, color: "#808080" });
  chrome.action.setBadgeText({ tabId: tabId, text: "..." });
  
  chrome.action.setIcon({ 
    tabId: tabId, 
    path: {
      "16": "icons/shield-inactive-16.png",
      "32": "icons/shield-inactive-32.png",
      "48": "icons/shield-inactive-48.png",
      "128": "icons/shield-inactive-128.png"
    } 
  });
}

async function enviarReporteParaAPI(url, vote) {
  try {
    const response = await fetch(`${API_ENDPOINT}/reportar_url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, voto: vote }),
    });
    return response.ok;
  } catch (error) {
    return false;
  }
}

function atualizarInterface(status, tabId) {
  let iconPaths = {
    "16": "icons/shield-inactive-16.png",
    "32": "icons/shield-inactive-32.png",
    "48": "icons/shield-inactive-48.png",
    "128": "icons/shield-inactive-128.png"
  };
  let badgeText = "";
  let badgeColor = "#757575";

  if (status === "phishing") {
    iconPaths = {
      "16": "icons/shield-danger-16.png",
      "32": "icons/shield-danger-32.png",
      "48": "icons/shield-danger-48.png",
      "128": "icons/shield-danger-128.png"
    };
    badgeText = "X";
    badgeColor = "#F04646";
  } else if (status === "suspect" || status === "suspicious") {
    iconPaths = {
      "16": "icons/shield-warning-16.png",
      "32": "icons/shield-warning-32.png",
      "48": "icons/shield-warning-48.png",
      "128": "icons/shield-warning-128.png"
    };
    badgeText = "!";
    badgeColor = "#F7E96D";
  } else if (status === "safe" || status === "secure") {
    iconPaths = {
      "16": "icons/shield-safe-16.png",
      "32": "icons/shield-safe-32.png",
      "48": "icons/shield-safe-48.png",
      "128": "icons/shield-safe-128.png"
    };
  }

  chrome.action.setIcon({ tabId: tabId, path: iconPaths });
  chrome.action.setBadgeText({ tabId: tabId, text: badgeText });
  chrome.action.setBadgeBackgroundColor({ tabId: tabId, color: badgeColor });
}

function limparBadge(tabId) {
  chrome.action.setBadgeText({ tabId: tabId, text: "" });
  chrome.action.setIcon({ tabId: tabId, path: "icons/shield-inactive-48.png" });
}