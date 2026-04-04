const API_ENDPOINT = 'http://127.0.0.1:8000/check_url';

const ICONS = {
  inactive: {
    16: 'icons/shield-inactive-16.png',
    32: 'icons/shield-inactive-32.png',
    48: 'icons/shield-inactive-48.png',
    128: 'icons/shield-inactive-128.png',
  },
  safe: {
    16: 'icons/shield-safe-16.png',
    32: 'icons/shield-safe-32.png',
    48: 'icons/shield-safe-48.png',
    128: 'icons/shield-safe-128.png',
  },
  warning: {
    16: 'icons/shield-warning-16.png',
    32: 'icons/shield-warning-32.png',
    48: 'icons/shield-warning-48.png',
    128: 'icons/shield-warning-128.png',
  },
  danger: {
    16: 'icons/shield-danger-16.png',
    32: 'icons/shield-danger-32.png',
    48: 'icons/shield-danger-48.png',
    128: 'icons/shield-danger-128.png',
  },
};

function updateIcon(tabId, status) {
  const iconPaths = ICONS[status] || ICONS.inactive;
  chrome.action.setIcon({ path: iconPaths, tabId: tabId });
}

/**
 * Listener for tab updates. This is the entry point for the analysis flow.
 * It triggers when a tab's loading process is complete.
 */
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // Ensure the page is fully loaded and the URL is a standard HTTP/HTTPS link.
  if (changeInfo.status === 'complete' && tab.url && (tab.url.startsWith('http:') || tab.url.startsWith('https:'))) {    
    // Check storage to see if protection is active before proceeding.
    chrome.storage.local.get(['protectionStatus'], (result) => {
      // Analysis is executed if 'protectionStatus' is true or if it is not yet defined (undefined),
      // treating the undefined state as "enabled" by default.
      if (result.protectionStatus !== false) {
        analyzePage(tabId, tab.url);
      } else {
        console.log('Phishio: Protection disabled. Skipping page analysis.');
        updateIcon(tabId, 'inactive');
      }
    });
  }
});

/**
 * Injects the content script to extract the DOM, then sends the data to the backend API.
 * This follows the flow described in Figure 2 of the TCC document.
 * @param {number} tabId - The ID of the tab to be analyzed.
 * @param {string} url - The URL of the page to be analyzed.
 */
async function analyzePage(tabId, url) {
  try {
    const [injectionResult] = await chrome.scripting.executeScript({
      target: { tabId: tabId },
      files: ['content.js'],
    });

    // After injection, send a message to the content script to get the DOM.
    if (injectionResult.result === undefined) { // Check if script was injected
        chrome.tabs.sendMessage(tabId, { action: "getDOM" }, async (response) => {
            if (chrome.runtime.lastError) {
                console.error("Phishio Error: ", chrome.runtime.lastError.message);
                return;
            }
            if (response && response.domContent) {
                // Step 1: Send URL/DOM to Backend API (as per Figure 2)
                const apiResponse = await fetch(API_ENDPOINT, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url, dom: response.domContent }),
                });

                const result = await apiResponse.json();

                // Map the API verdict to a standard status and update the UI.
                // The API can return 'seguro', 'suspeito', 'perigoso'. We standardize to 'safe', 'suspicious', 'phishing'.
                let standardStatus;
                switch (result.status) {
                    case 'perigoso':
                    case 'danger':
                        standardStatus = 'danger';
                        break;
                    case 'suspeito':
                    case 'warning':
                        standardStatus = 'warning';
                        break;
                    case 'seguro':
                    default:
                        standardStatus = 'safe';
                        break;
                }

                // Store the URL status in local storage so popup.js can access it.
                // The URL itself is used as the key for easy retrieval in the popup.
                await chrome.storage.local.set({ [url]: standardStatus });
                console.log(`Phishio: URL status for ${url} (${standardStatus}) saved to local storage.`);

                // Step 4: Update the extension icon to reflect the verdict.
                updateIcon(tabId, standardStatus);

                if (standardStatus === 'danger') {
                    showPhishingAlert(tabId, url, result.score);
                }
            }
        });
    }
  } catch (error) {
    console.error("Phishio Error: Failed to inject script or analyze page.", error);
  }
}

/**
 * Displays a visual notification to the user, as described in the TCC
 * under "Alertas Visuais".
 * @param {number} tabId - The ID of the tab where the phishing was detected.
 * @param {string} url - The malicious URL.
 * @param {number} score - The confidence score from the API.
 */
function showPhishingAlert(tabId, url, score) {
  chrome.notifications.create(`phishio-alert-${tabId}`, {
    type: 'basic',
    iconUrl: 'icons/shield-danger-128.png', // Use the danger icon in the notification
    title: 'Phishio - Alerta de Phishing',
    message: `O site ${url} foi identificado como uma potencial ameaça com score de ${score.toFixed(2)}.`,
    priority: 2,
  });
}