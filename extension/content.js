/** Script de conteúdo responsável por extrair o DOM da página atual apenas se solicitado. */
async function iniciarAnalise() {
  if (!window.location.href.startsWith("http")) return;
  if (!document.body) return;

  const url = window.location.href;

  try {
    const resposta = await sendMessageComTimeout(
      { action: "analisarPagina", url: url },
      2000,
    );

    if (resposta && resposta.needsContent) {
      coletarEEnviarConteudo(url);
    }
  } catch (error) {
    console.warn(
      "Phishio: Falha no handshake com o Service Worker:",
      error.message,
    );
  }
}

function sendMessageComTimeout(mensagem, ms) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("Timeout de conexão")), ms);

    chrome.runtime.sendMessage(mensagem, (resposta) => {
      clearTimeout(timer);
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve(resposta);
      }
    });
  });
}

function coletarEEnviarConteudo(url) {
  const cloneDoc = document.documentElement.cloneNode(true);
  cloneDoc.querySelectorAll("script, style").forEach((el) => el.remove());
  const dadosCompletos = {
    url: url,
    content: document.body.innerText,
    dom: document.documentElement.outerHTML,
  };
  chrome.runtime.sendMessage({
    action: "enviarDadosCompletos",
    dados: dadosCompletos,
  });
}

iniciarAnalise();
