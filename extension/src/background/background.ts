/**
 * Background service worker for GroveAssistant.
 *
 * Handles:
 * - API communication with backend
 * - Message passing from content scripts
 * - Storage management
 */

import * as api from "../shared/api";
import type { MessageType, MessageResponse, AnalyzeResponse } from "../shared/types";

/**
 * Handle messages from content scripts and popup.
 */
browser.runtime.onMessage.addListener(
  (message: MessageType, _sender): Promise<MessageResponse> => {
    return handleMessage(message);
  }
);

async function handleMessage(message: MessageType): Promise<MessageResponse> {
  try {
    switch (message.type) {
      case "ANALYZE_PRODUCT": {
        const result = await api.analyzeProduct({
          url: message.payload.url,
          html: message.payload.html,
        });
        return { success: true, data: result };
      }

      case "GET_PROFILE": {
        const profile = await api.getProfile();
        return { success: true, data: profile };
      }

      case "TEST_CONNECTION": {
        const status = await api.testConnection();
        return { success: true, data: status };
      }

      case "GET_SETTINGS": {
        const { getSettings } = await import("../shared/storage");
        const settings = await getSettings();
        return { success: true, data: settings };
      }

      default:
        return { success: false, error: "Unknown message type" };
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    console.error("[GroveAssistant] Background error:", errorMessage);
    return { success: false, error: errorMessage };
  }
}

/**
 * Handle extension installation/update.
 */
browser.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") {
    console.log("[GroveAssistant] Extension installed");
    // Could open welcome/setup page here
  } else if (details.reason === "update") {
    console.log("[GroveAssistant] Extension updated to", browser.runtime.getManifest().version);
  }
});

console.log("[GroveAssistant] Background script loaded");
