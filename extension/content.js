/**
 * Listens for a message from the background service worker.
 * When it receives the 'getDOM' action, it extracts the text content of the page
 * and sends it back.
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getDOM") {
    // Extracting the text content is more efficient and relevant for TF-IDF analysis
    // than sending the entire HTML structure.
    const domContent = document.body.innerText;
    sendResponse({ domContent: domContent });
  }
  return true; // Keep the message channel open for the asynchronous response.
});