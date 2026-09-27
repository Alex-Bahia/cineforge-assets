/**
 * License management — validates keys against the CineForge licensing server
 */

const LICENSE_API = 'https://cineforge.app/api/license';
const CACHE_TTL = 24 * 60 * 60 * 1000; // 24h

export const LicenseManager = {

  async check() {
    const { license } = await chrome.storage.local.get('license');
    if (!license) return false;

    // Use cached validation within TTL
    const now = Date.now();
    if (license.validatedAt && (now - license.validatedAt) < CACHE_TTL) {
      return license.active === true;
    }

    // Re-validate
    return this.validate(license.key);
  },

  async activate(key) {
    const result = await this.validate(key);
    if (result) {
      await chrome.storage.local.set({
        license: { key, active: true, validatedAt: Date.now() },
      });
    }
    return result;
  },

  async validate(key) {
    try {
      const response = await fetch(`${LICENSE_API}/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          key,
          extensionId: chrome.runtime.id,
          version: chrome.runtime.getManifest().version,
        }),
      });

      if (!response.ok) return false;

      const data = await response.json();

      if (data.valid) {
        await chrome.storage.local.set({
          license: { key, active: true, validatedAt: Date.now(), plan: data.plan, expiresAt: data.expiresAt },
        });
        return true;
      }

      await chrome.storage.local.set({ license: { key, active: false, validatedAt: Date.now() } });
      return false;

    } catch {
      // Network error — if previously valid, allow offline use
      const { license } = await chrome.storage.local.get('license');
      return license?.active === true;
    }
  },

  async getLicenseInfo() {
    const { license } = await chrome.storage.local.get('license');
    return license || null;
  },

  async revoke() {
    await chrome.storage.local.remove('license');
  },
};
