document.addEventListener('DOMContentLoaded', () => {
  const btnAgree = document.getElementById('btn-agree');
  const container = document.querySelector('.container');

  btnAgree.addEventListener('click', () => {
    chrome.storage.local.set({ lgpdConsent: true, protectionActive: true }, () => {
      
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

    });
  });
});