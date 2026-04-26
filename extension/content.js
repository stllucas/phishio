/** Script de conteúdo responsável por extrair o DOM da página atual apenas se solicitado. */
async function iniciarAnalise() {
  if (!window.location.href.startsWith("http")) return;
  if (!document.body) return;

  const url = window.location.href;

  chrome.runtime.sendMessage(
    { 
      action: "analisarPagina", 
      url: url 
    }, 
    (resposta) => {
      if (resposta && resposta.needsContent) {
        coletarEEnviarConteudo(url);
      }
    }
  );
}

function coletarEEnviarConteudo(url) {
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