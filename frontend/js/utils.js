/**
 * CEREBRO — Utility Helpers
 */

const Utils = {
  // Safe DOM element selection
  $(selector) {
    return document.querySelector(selector);
  },
  $$(selector) {
    return Array.from(document.querySelectorAll(selector));
  },

  // Toast Notification
  showToast(message, type = 'info') {
    let container = document.getElementById('cerebro-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'cerebro-toast-container';
      container.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        z-index: 9999;
      `;
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const colors = {
      success: '#10b981',
      error: '#ef4444',
      info: '#8b5cf6',
      warning: '#f59e0b'
    };

    toast.style.cssText = `
      background: #111a33;
      border: 1px solid ${colors[type] || '#8b5cf6'};
      color: #ffffff;
      padding: 12px 18px;
      border-radius: 10px;
      font-size: 0.84rem;
      font-weight: 500;
      box-shadow: 0 4px 16px rgba(0,0,0,0.4);
      display: flex;
      align-items: center;
      gap: 10px;
      animation: fadeInToast 0.2s ease-out;
    `;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  },

  // Color generator for avatar initials
  getAvatarGradient(name) {
    const gradients = [
      'linear-gradient(135deg, #3b82f6, #1d4ed8)',
      'linear-gradient(135deg, #8b5cf6, #6d28d9)',
      'linear-gradient(135deg, #06b6d4, #0e7490)',
      'linear-gradient(135deg, #f59e0b, #d97706)',
      'linear-gradient(135deg, #10b981, #047857)',
      'linear-gradient(135deg, #ec4899, #be185d)'
    ];
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    return gradients[Math.abs(hash) % gradients.length];
  },

  // Format initials
  getInitials(name) {
    if (!name) return 'U';
    const parts = name.trim().split(' ');
    if (parts.length > 1) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  },

  // Show / Hide Loading Modal
  setLoading(isLoading, title = 'Analyzing Conversation...', subtitle = 'Evaluating contextual tone, sarcasm, and emotional arc') {
    const overlay = document.getElementById('loading-overlay');
    if (!overlay) return;
    if (isLoading) {
      document.getElementById('loading-title').innerText = title;
      document.getElementById('loading-subtitle').innerText = subtitle;
      overlay.classList.add('active');
    } else {
      overlay.classList.remove('active');
    }
  }
};
