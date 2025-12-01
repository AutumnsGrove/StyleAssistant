/**
 * Browser storage utilities for GroveAssistant.
 *
 * Uses Firefox storage.local API for persistent data.
 */

import type { ExtensionSettings, UserProfile } from "./types";

const DEFAULT_SETTINGS: ExtensionSettings = {
  apiEndpoint: "http://localhost:8000",
  autoAnalyze: true,
  showCosts: true,
};

/**
 * Get extension settings from storage.
 */
export async function getSettings(): Promise<ExtensionSettings> {
  const result = await browser.storage.local.get("settings");
  return { ...DEFAULT_SETTINGS, ...(result.settings || {}) };
}

/**
 * Save extension settings to storage.
 */
export async function saveSettings(
  settings: Partial<ExtensionSettings>
): Promise<void> {
  const current = await getSettings();
  await browser.storage.local.set({
    settings: { ...current, ...settings },
  });
}

/**
 * Get user profile from storage.
 */
export async function getProfile(): Promise<UserProfile | null> {
  const result = await browser.storage.local.get("profile");
  return result.profile || null;
}

/**
 * Save user profile to storage.
 */
export async function saveProfile(profile: UserProfile): Promise<void> {
  await browser.storage.local.set({ profile });
}

/**
 * Clear user profile from storage.
 */
export async function clearProfile(): Promise<void> {
  await browser.storage.local.remove("profile");
}

/**
 * Get session ID for cost tracking.
 * Creates new session ID if none exists or if expired.
 */
export async function getSessionId(): Promise<string> {
  const result = await browser.storage.local.get(["sessionId", "sessionStart"]);

  // Session expires after 1 hour
  const ONE_HOUR = 60 * 60 * 1000;
  const now = Date.now();

  if (
    result.sessionId &&
    result.sessionStart &&
    now - result.sessionStart < ONE_HOUR
  ) {
    return result.sessionId;
  }

  // Generate new session ID
  const sessionId = crypto.randomUUID();
  await browser.storage.local.set({
    sessionId,
    sessionStart: now,
  });

  return sessionId;
}
