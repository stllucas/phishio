/** Script de conteúdo responsável por extrair o DOM da página atual apenas se solicitado. */
/**
 * Inicia a análise da página ao carregar, validando a URL e solicitando autorização do Service Worker.
 */
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

/**
 * Envia uma mensagem para o script de background aguardando uma resposta até o timeout.
 * @param {Object} mensagem - Objeto contendo os dados a serem enviados.
 * @param {number} ms - Tempo limite em milissegundos.
 * @returns {Promise<any>} A resposta fornecida pelo Service Worker.
 */
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

/**
 * Extrai os textos visíveis e a estrutura DOM limitando seu tamanho para evitar sobrecarga no servidor e os envia.
 * @param {string} url - A URL completa da página a ser analisada.
 */
function coletarEEnviarConteudo(url) {
  const cloneDoc = document.documentElement.cloneNode(true);
  cloneDoc
    .querySelectorAll("script, style, svg, img, video, audio, canvas, iframe")
    .forEach((el) => el.remove());

  let textoConteudo = document.body.innerText || "";
  let textoDom = cloneDoc.outerHTML || "";

  /** Limita o tamanho do payload para evitar o erro HTTP 413 (Payload Too Large) no Nginx/Servidor. */
  const MAX_CHARACTERS = 150000;

  const dadosCompletos = {
    url: url,
    content: textoConteudo.substring(0, MAX_CHARACTERS),
    dom: textoDom.substring(0, MAX_CHARACTERS),
  };
  chrome.runtime.sendMessage({
    action: "enviarDadosCompletos",
    dados: dadosCompletos,
  });
}

iniciarAnalise();
