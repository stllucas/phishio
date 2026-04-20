// background.js
const API_ENDPOINT = "https://phishio.duckdns.org";

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  // 1. Verifica se a página carregou e se é uma URL válida
  if (
    changeInfo.status === "complete" &&
    tab.url &&
    tab.url.startsWith("http")
  ) {
    // 2. Verifica se a proteção está ativada antes de fazer qualquer análise
    const storage = await chrome.storage.local.get(["protectionStatus"]);
    const isEnabled = storage.protectionStatus !== false;

    if (!isEnabled) {
      console.log(
        "Phishio: Proteção desativada pelo usuário. Ignorando análise.",
      );
      updateIcon(tabId, "inactive");
      return;
    }

    // 3. Se estiver ativo, segue com a análise normal
    getPhishingStatus(tabId, tab.url);
  }
});
async function getPhishingStatus(tabId, url) {
  try {
    const response = await chrome.tabs.sendMessage(tabId, {
      action: "getDomContent",
    });
    if (response && response.dom) {
      const apiResponse = await fetch(`${API_ENDPOINT}/check_url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url, dom: response.dom }),
      });

      if (!apiResponse.ok)
        throw new Error(`API Error: ${apiResponse.statusText}`);

      const result = await apiResponse.json();
      const { status } = result;

      await chrome.storage.local.set({ [url]: status });
      updateIcon(tabId, status);

      if (status === "phishing" || status === "suspicious") {
        chrome.tabs.sendMessage(tabId, {
          action: "displayPhishingOverlay",
          status: status,
          url: url,
        });
      }
    }
  } catch (error) {
    console.warn(`Phishio: Erro na aba ${tabId} (${url}): ${error.message}`);
    updateIcon(tabId, "inactive");
  }
}

function updateIcon(tabId, status) {
  const iconPaths = {
    safe: "icons/shield-safe-48.png",
    suspicious: "icons/shield-warning-48.png",
    phishing: "icons/shield-danger-48.png",
    inactive: "icons/shield-inactive-48.png",
  };
  const path = iconPaths[status] || iconPaths["inactive"];
  chrome.action.setIcon({ tabId: tabId, path: path });
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "reportUrl") {
    handleUrlReport(message.url, message.vote)
      .then((response) => sendResponse({ success: true, data: response }))
      .catch((error) => sendResponse({ success: false, error: error.message }));
    return true;
  }
});

async function handleUrlReport(url, vote) {
  const apiResponse = await fetch(`${API_ENDPOINT}/reportar_url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: url, voto: vote }),
  });
  if (!apiResponse.ok) throw new Error(`API Error: ${apiResponse.statusText}`);
  return await apiResponse.json();
}
