export const Storage = {
  async get(key) { const r = await chrome.storage.local.get(key); return r[key]; },
  async set(key, value) { return chrome.storage.local.set({ [key]: value }); },
  async addJob(job) { const jobs = (await this.get('jobs')) || []; jobs.unshift(job); await this.set('jobs', jobs.slice(0, 50)); },
  async updateJob(id, updates) {
    const jobs = (await this.get('jobs')) || [];
    const idx = jobs.findIndex(j => j.id === id);
    if (idx !== -1) { jobs[idx] = { ...jobs[idx], ...updates }; await this.set('jobs', jobs); }
  },
  async getJob(id) { const jobs = (await this.get('jobs')) || []; return jobs.find(j => j.id === id); },
};
