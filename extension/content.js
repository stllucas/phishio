// content.js - Execução limpa e silenciosa
function capturarEEnviar() {
  // Só executa em páginas web válidas
  if (!window.location.href.startsWith("http")) return;
  if (!document.body) return; // Heurística: Prevenção de erros caso a página carregue anomalias sem body formado

  const dadosParaAnalise = {
    url: window.location.href,
    content: document.body.innerText,
    dom: document.documentElement.outerHTML,
  };

  // Envia silenciosamente para o background.js analisar
  chrome.runtime.sendMessage({
    action: "analisarPagina",
    dados: dadosParaAnalise,
  });
}

// Inicia automaticamente quando a página carrega
capturarEEnviar();
