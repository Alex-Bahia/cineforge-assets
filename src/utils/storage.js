/**
 * Storage helpers — wraps chrome.storage.local
 */
export const Storage = {
  async get(key) {
    const result = await chrome.storage.local.get(key);
    return result[key];
  },

  async set(key, value) {
    return chrome.storage.local.set({ [key]: value });
  },

  async addJob(job) {
    const jobs = (await this.get('jobs')) || [];
    jobs.unshift(job);
    // Keep last 50 jobs
    await this.set('jobs', jobs.slice(0, 50));
  },

  async updateJob(id, updates) {
    const jobs = (await this.get('jobs')) || [];
    const idx = jobs.findIndex(j => j.id === id);
    if (idx !== -1) {
      jobs[idx] = { ...jobs[idx], ...updates };
      await this.set('jobs', jobs);
    }
  },

  async getJob(id) {
    const jobs = (await this.get('jobs')) || [];
    return jobs.find(j => j.id === id);
  },

  async clearCompleted() {
    const jobs = (await this.get('jobs')) || [];
    await this.set('jobs', jobs.filter(j => j.status === 'processing'));
  },
};
