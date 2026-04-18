// Simular backend
const sitesSuspeitos = ["github.com", "teste.com"];
const sitesPerigosos = ["malicioso.com", "phishing.net"];

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (
    changeInfo.status === "complete" &&
    tab.url &&
    tab.url.startsWith("http")
  ) {
    chrome.storage.local.get(["protectionActive"], function (result) {
      if (result.protectionActive) {
        const url = new URL(tab.url).hostname;

        if (sitesPerigosos.includes(url)) {
          chrome.action.setBadgeBackgroundColor({ color: "#F04646" });
          chrome.action.setBadgeText({ text: "X" });
        } else if (sitesSuspeitos.includes(url)) {
          chrome.action.setBadgeBackgroundColor({ color: "#F7E96D" });
          chrome.action.setBadgeText({ text: "!" });
        } else {
          chrome.action.setBadgeText({ text: "" });
        }
      } else {
        chrome.action.setBadgeText({ text: "" });
      }
    });
  }
});
