/**
 * Popup script for GroveAssistant.
 *
 * Handles:
 * - Settings display/modification
 * - Profile status
 * - Connection testing
 */

import type { MessageResponse, UserProfile, ExtensionSettings } from "../shared/types";

// DOM elements
const elements = {
  status: document.getElementById("status") as HTMLElement,
  profileStatus: document.getElementById("profile-status") as HTMLElement,
  connectionStatus: document.getElementById("connection-status") as HTMLElement,
  testConnectionBtn: document.getElementById("test-connection") as HTMLButtonElement,
  takeQuizBtn: document.getElementById("take-quiz") as HTMLButtonElement,
  apiEndpoint: document.getElementById("api-endpoint") as HTMLInputElement,
  autoAnalyze: document.getElementById("auto-analyze") as HTMLInputElement,
  showCosts: document.getElementById("show-costs") as HTMLInputElement,
  saveSettingsBtn: document.getElementById("save-settings") as HTMLButtonElement,
};

/**
 * Send message to background script.
 */
async function sendMessage<T>(message: unknown): Promise<T> {
  const response = (await browser.runtime.sendMessage(message)) as MessageResponse;
  if (!response.success) {
    throw new Error(response.error);
  }
  return response.data as T;
}

/**
 * Update connection status display.
 */
async function updateConnectionStatus(): Promise<void> {
  elements.connectionStatus.textContent = "Checking...";
  elements.connectionStatus.className = "status-checking";

  try {
    const result = await sendMessage<{ status: string; message: string }>({
      type: "TEST_CONNECTION",
    });

    if (result.status === "ok") {
      elements.connectionStatus.textContent = "Connected";
      elements.connectionStatus.className = "status-connected";
    } else {
      elements.connectionStatus.textContent = result.message || "Not configured";
      elements.connectionStatus.className = "status-error";
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : "Connection failed";
    elements.connectionStatus.textContent = message;
    elements.connectionStatus.className = "status-error";
  }
}

/**
 * Update profile status display.
 */
async function updateProfileStatus(): Promise<void> {
  try {
    const profile = await sendMessage<UserProfile | null>({ type: "GET_PROFILE" });

    if (profile) {
      elements.profileStatus.textContent = "Profile active";
      elements.profileStatus.className = "status-active";
      elements.takeQuizBtn.textContent = "Retake Quiz";
    } else {
      elements.profileStatus.textContent = "No profile (basic mode)";
      elements.profileStatus.className = "status-inactive";
      elements.takeQuizBtn.textContent = "Take Style Quiz";
    }
  } catch (error) {
    elements.profileStatus.textContent = "Unable to load profile";
    elements.profileStatus.className = "status-error";
  }
}

/**
 * Load settings into form.
 */
async function loadSettings(): Promise<void> {
  try {
    const settings = await sendMessage<ExtensionSettings>({ type: "GET_SETTINGS" });

    elements.apiEndpoint.value = settings.apiEndpoint;
    elements.autoAnalyze.checked = settings.autoAnalyze;
    elements.showCosts.checked = settings.showCosts;
  } catch (error) {
    console.error("[GroveAssistant] Failed to load settings:", error);
  }
}

/**
 * Save settings from form.
 */
async function saveSettings(): Promise<void> {
  const settings: ExtensionSettings = {
    apiEndpoint: elements.apiEndpoint.value.trim(),
    autoAnalyze: elements.autoAnalyze.checked,
    showCosts: elements.showCosts.checked,
  };

  try {
    await browser.storage.local.set({ settings });
    showStatus("Settings saved!", "success");
    await updateConnectionStatus();
  } catch (error) {
    showStatus("Failed to save settings", "error");
  }
}

/**
 * Show temporary status message.
 */
function showStatus(message: string, type: "success" | "error"): void {
  elements.status.textContent = message;
  elements.status.className = `status-${type}`;
  elements.status.style.display = "block";

  setTimeout(() => {
    elements.status.style.display = "none";
  }, 3000);
}

/**
 * Open quiz page (placeholder).
 */
function openQuiz(): void {
  // TODO: Open quiz page in new tab
  browser.tabs.create({
    url: browser.runtime.getURL("quiz/quiz.html"),
  });
}

/**
 * Initialize popup.
 */
async function init(): Promise<void> {
  // Load initial state
  await Promise.all([loadSettings(), updateConnectionStatus(), updateProfileStatus()]);

  // Add event listeners
  elements.testConnectionBtn.addEventListener("click", updateConnectionStatus);
  elements.takeQuizBtn.addEventListener("click", openQuiz);
  elements.saveSettingsBtn.addEventListener("click", saveSettings);
}

// Initialize on load
document.addEventListener("DOMContentLoaded", init);
