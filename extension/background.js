const API_ENDPOINT = "https://phishio.duckdns.org";

// 1. Ouvinte para receber os dados capturados pelo content.js (URL + Texto + DOM)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "analisarPagina") {
    // Verifica se a proteção está ativa no storage (Mantendo a criação do Pedro)
    chrome.storage.local.get(["protectionActive"], function (result) {
      if (result.protectionActive) {
        processarAnalise(request.dados, sender.tab.id);
      } else {
        limparBadge();
      }
    });
  }
  if (request.action === "reportUrl") {
    enviarReporteParaAPI(request.url, request.vote).then((sucesso) => {
      if (sucesso) {
        // Incrementa o contador de contribuições
        chrome.storage.local.get(["totalAvaliacoes"], (res) => {
          let total = res.totalAvaliacoes || 0;
          chrome.storage.local.set({ totalAvaliacoes: total + 1 });
        });
      }
      sendResponse({ success: sucesso });
    });
    return true; // Mantém o canal aberto para resposta assíncrona
  }
});

// 2. Conexão com o backend (Servidor na DigitalOcean)
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

    const resultado = await response.json();

    // Contador do joinha
    if (response.ok) {
      chrome.storage.local.get(["totalAvaliacoes"], (result) => {
        let total = result.totalAvaliacoes || 0;
        chrome.storage.local.set({ totalAvaliacoes: total + 1 });
      });
    }

    chrome.storage.local.set({ [`status_${tabId}`]: resultado.status });

    atualizarInterface(resultado.status);
  } catch (error) {
    console.error("Erro na comunicação com o Phishio:", error);
    chrome.action.setBadgeText({ text: "ERR" });
  }
}

// Função para comunicar o voto ao servidor
async function enviarReporteParaAPI(url, vote) {
  try {
    const response = await fetch(`${API_ENDPOINT}/reportar_url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, vote }),
    });
    return response.ok;
  } catch (error) {
    console.error("Erro ao reportar:", error);
    return false;
  }
}

// Lógica do front
function atualizarInterface(status) {
  if (status === "phishing") {
    iconPath = "icons/shield-danger-48.png";
    chrome.action.setBadgeBackgroundColor({ color: "#F04646" });
    chrome.action.setBadgeText({ text: "X" });
  } else if (status === "suspect") {
    iconPath = "icons/shield-warning-48.png";
    chrome.action.setBadgeBackgroundColor({ color: "#F7E96D" });
    chrome.action.setBadgeText({ text: "!" });
  } else {
    limparBadge();
  }

  // Atualiza o ícone da extensão com base no status
  chrome.action.setIcon({ path: iconPath });
}

function limparBadge() {
  chrome.action.setBadgeText({ text: "" });
}
