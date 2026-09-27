/**
 * CEREBRO — API Client Service
 */

const Api = {
  getBaseUrl() {
    return localStorage.getItem('cerebro_api_url') || '';
  },

  setBaseUrl(url) {
    if (url && url.endsWith('/')) {
      url = url.slice(0, -1);
    }
    localStorage.setItem('cerebro_api_url', url || '');
  },

  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${this.getBaseUrl()}/api/upload`, {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to upload chat file');
    }
    return data;
  },

  async loadSample() {
    const res = await fetch(`${this.getBaseUrl()}/api/sample`);
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to load sample conversation');
    }
    return data;
  },

  async analyze(payload = {}) {
    const res = await fetch(`${this.getBaseUrl()}/api/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Analysis failed. Please check backend connection.');
    }
    return data.data;
  },

  async getSettings() {
    const res = await fetch(`${this.getBaseUrl()}/api/settings`);
    return await res.json();
  },

  async saveSettings(settings) {
    const res = await fetch(`${this.getBaseUrl()}/api/settings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(settings)
    });
    return await res.json();
  },

  async checkHealth() {
    try {
      const res = await fetch(`${this.getBaseUrl()}/api/health`);
      return await res.json();
    } catch (e) {
      return { status: 'offline', error: e.message };
    }
  }
};
