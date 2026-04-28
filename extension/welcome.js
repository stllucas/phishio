document.addEventListener('DOMContentLoaded', () => {
  const btnAgree = document.getElementById('btn-agree');

  btnAgree.addEventListener('click', () => {
    chrome.storage.local.set({ lgpdConsent: true, protectionActive: true }, () => {
      alert("Configuração concluída! O Phishio já está te protegendo.");
      window.close(); 
    });
  });
});