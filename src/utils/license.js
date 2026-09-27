const LICENSE_API = 'https://cineforge.app/api/license';
const CACHE_TTL = 24 * 60 * 60 * 1000;

export const LicenseManager = {
  async check() {
    const { license } = await chrome.storage.local.get('license');
    if (!license) return false;
    if (license.validatedAt && (Date.now() - license.validatedAt) < CACHE_TTL) return license.active === true;
    return this.validate(license.key);
  },
  async activate(key) {
    const ok = await this.validate(key);
    if (ok) await chrome.storage.local.set({ license: { key, active: true, validatedAt: Date.now() } });
    return ok;
  },
  async validate(key) {
    try {
      const r = await fetch(`${LICENSE_API}/validate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key, extensionId: chrome.runtime.id, version: chrome.runtime.getManifest().version }) });
      if (!r.ok) return false;
      const d = await r.json();
      if (d.valid) { await chrome.storage.local.set({ license: { key, active: true, validatedAt: Date.now(), plan: d.plan } }); return true; }
      await chrome.storage.local.set({ license: { key, active: false, validatedAt: Date.now() } }); return false;
    } catch {
      const { license } = await chrome.storage.local.get('license');
      return license?.active === true;
    }
  },
  async revoke() { await chrome.storage.local.remove('license'); },
};
