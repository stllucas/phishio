document.addEventListener("DOMContentLoaded", () => {
  const btnAgree = document.getElementById("btn-agree");
  const btnDecline = document.getElementById("btn-decline");
  const container = document.querySelector(".container");

  document.addEventListener("DOMContentLoaded", () => {
    const btnAgree = document.getElementById("btn-agree");
    const btnDecline = document.getElementById("btn-decline");
    const container = document.querySelector(".container");
    const API_ENDPOINT = "https://phishio.duckdns.org";

    btnAgree.addEventListener("click", () => {
      fetch(`${API_ENDPOINT}/registrar_consentimento`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          versao_termos: "v1.0",
          user_agent: navigator.userAgent,
        }),
      })
        .then((response) => {
          if (!response.ok) {
            console.warn("Aviso: Falha ao registrar consentimento no backend.");
          }
        })
        .catch((error) => {
          console.error(
            "Erro na comunicação com a API de consentimento:",
            error,
          );
        })
        .finally(() => {
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
        });
    });
  });

  btnDecline.addEventListener("click", () => {
    chrome.management.uninstallSelf({ showConfirmDialog: true }, () => {
      if (chrome.runtime.lastError) {
        console.log("O usuário cancelou a desinstalação.");
      }
    });
  });
});
