/** Script de conteúdo responsável por extrair o DOM da página atual. */
function capturarEEnviar() {
  if (!window.location.href.startsWith("http")) return;
  if (!document.body) return;

  const dadosParaAnalise = {
    url: window.location.href,
    content: document.body.innerText,
    dom: document.documentElement.outerHTML,
  };

  chrome.runtime.sendMessage({
    action: "analisarPagina",
    dados: dadosParaAnalise,
  });
}

capturarEEnviar();
