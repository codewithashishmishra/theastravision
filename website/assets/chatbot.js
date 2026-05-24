(function () {
  const faqs = (window.AASTRAA_FAQS && window.AASTRAA_FAQS.HR_FAQS) || [];

  const chatToggle = document.getElementById('chat-toggle');
  const closeChat = document.getElementById('close-chat');
  const chatWindow = document.getElementById('chat-window');
  const chatMessages = document.getElementById('chat-messages');
  const faqListContainer = document.getElementById('faq-list');
  const faqSearch = document.getElementById('faq-search');
  const typingIndicator = document.getElementById('typing-indicator');
  const faqCountLabel = document.getElementById('faq-count-label');

  if (!chatToggle || !faqListContainer || faqs.length === 0) return;

  if (faqCountLabel) {
    faqCountLabel.textContent = faqs.length + ' FAQs';
  }

  chatToggle.addEventListener('click', () => {
    chatWindow.classList.add('active');
    const badge = chatToggle.querySelector('span');
    if (badge) badge.classList.add('hidden');
  });

  closeChat.addEventListener('click', () => {
    chatWindow.classList.remove('active');
  });

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function renderFaqs(filterText = '') {
    faqListContainer.innerHTML = '';
    const q = filterText.toLowerCase();
    const filtered = faqs.filter(
      (faq) => faq.q.toLowerCase().includes(q) || faq.a.toLowerCase().includes(q)
    );

    if (filtered.length === 0) {
      faqListContainer.innerHTML =
        '<p class="text-xs text-slate-400 text-center py-4">No matching questions found.</p>';
      return;
    }

    filtered.forEach((faq) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className =
        'w-full text-left text-xs bg-slate-50 hover:bg-primary-50 text-slate-700 hover:text-primary-700 p-2.5 rounded-lg border border-slate-100 transition-colors shadow-sm whitespace-normal';
      btn.innerHTML =
        '<i class="fa-solid fa-circle-question text-primary-400 mr-1.5" aria-hidden="true"></i> ' +
        escapeHtml(faq.q);
      btn.onclick = () => handleFaqClick(faq);
      faqListContainer.appendChild(btn);
    });
  }

  function handleFaqClick(faq) {
    if (faqSearch) faqSearch.value = '';
    renderFaqs();

    const userMsg = document.createElement('div');
    userMsg.className = 'flex justify-end mb-2';
    userMsg.innerHTML =
      '<div class="bg-primary-600 text-white p-3 rounded-2xl rounded-tr-none shadow-sm text-sm max-w-[85%]">' +
      escapeHtml(faq.q) +
      '</div>';
    chatMessages.appendChild(userMsg);
    scrollToBottom();

    typingIndicator.classList.remove('hidden');

    setTimeout(() => {
      typingIndicator.classList.add('hidden');
      const botMsg = document.createElement('div');
      botMsg.className = 'flex gap-3 mb-2';
      botMsg.innerHTML =
        '<div class="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center shrink-0 mt-1"><i class="fa-solid fa-robot text-xs" aria-hidden="true"></i></div>' +
        '<div class="bg-white p-3 rounded-2xl rounded-tl-none shadow-sm border border-slate-100 text-sm text-slate-700 max-w-[85%] leading-relaxed">' +
        escapeHtml(faq.a) +
        '</div>';
      chatMessages.appendChild(botMsg);
      scrollToBottom();
    }, 800 + Math.random() * 500);
  }

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  renderFaqs();
  if (faqSearch) {
    faqSearch.addEventListener('input', (e) => renderFaqs(e.target.value));
    faqSearch.placeholder = 'Search ' + faqs.length + ' FAQs...';
  }
})();
