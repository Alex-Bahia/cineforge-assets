export const Toast = {
  show(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = { success: '✓', error: '✕', info: 'ℹ' }[type] || '';
    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = '200ms ease'; setTimeout(() => toast.remove(), 200); }, duration);
  },
};
