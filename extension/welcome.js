/**
 * Script responsável pela interface de boas-vindas, coletando o aceite da LGPD 
 * pelo usuário e inicializando as flags de proteção da extensão.
 */
document.addEventListener("DOMContentLoaded", () => {
  const btnAgree = document.getElementById("btn-agree");
  const btnDecline = document.getElementById("btn-decline");
  const container = document.querySelector(".container");
  const API_ENDPOINT = "https://phishio.duckdns.org";

  btnAgree.addEventListener("click", async (e) => {
    e.preventDefault();
    
    btnAgree.disabled = true;
    const originalText = btnAgree.innerHTML;
    btnAgree.innerHTML = "Processando...";

    try {
      const response = await fetch(`${API_ENDPOINT}/registrar_consentimento`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          versao_termos: "v1.0",
          user_agent: navigator.userAgent,
        }),
      });

      if (!response.ok) {
        throw new Error(`Erro do servidor: ${response.status}`);
      }

      chrome.storage.local.set(
        { lgpdConsent: true, protectionActive: true },
        () => {
          container.innerHTML = `
            <div style="font-family: 'Righteous', sans-serif; color: #52c47a; font-size: 32px; margin-bottom: 20px;">
              ✔ Tudo Certo!
            </div>
            <p style="font-size: 14px; color: #777;">
              Fechando esta aba automaticamente...
            </p>
          `;

          setTimeout(() => {
            window.close();
          }, 1000);
        },
      );
    } catch (error) {
      console.error("Erro na comunicação com a API de consentimento:", error);
      btnAgree.disabled = false;
      btnAgree.innerHTML = originalText;
      alert("Erro ao registrar consentimento no banco de dados. A API pode estar indisponível.");
    }
  });

  btnDecline.addEventListener("click", (e) => {
    e.preventDefault();
    chrome.management.uninstallSelf({ showConfirmDialog: true }, () => {
      if (chrome.runtime.lastError) {
        console.log("O usuário cancelou a desinstalação.");
      }
    });
  });
});
