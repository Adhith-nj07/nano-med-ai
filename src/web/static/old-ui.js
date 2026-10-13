document.addEventListener('DOMContentLoaded', async () => {
  const statusEl = document.getElementById('api-status');
  const health = await fetch('/api/health').then(r => r.json()).catch(() => ({ status: 'offline' }));
  const online = health.status === 'healthy';
  statusEl.textContent = online ? 'API online' : 'Offline';
  statusEl.className = 'pill ' + (online ? 'online' : 'warn');

  const simLink = document.getElementById('open-sim-link');
  if (simLink) {
    simLink.addEventListener('click', () => {
      window.location.href = '/simulation-demo';
    });
  }
});
