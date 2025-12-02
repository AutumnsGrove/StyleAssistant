/**
 * API client for GroveAssistant backend.
 */

import type { AnalyzeRequest, AnalyzeResponse, UserProfile } from "./types";
import { getSettings } from "./storage";

/** Default timeout for API requests (30 seconds) */
const DEFAULT_TIMEOUT = 30000;

/** Extended timeout for analysis requests (2 minutes) */
const ANALYSIS_TIMEOUT = 120000;

/**
 * Fetch with timeout support.
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeout: number
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("Request timed out. Please check if the backend is running.");
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Make a request to the backend API.
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  timeout = DEFAULT_TIMEOUT
): Promise<T> {
  const settings = await getSettings();
  const url = `${settings.apiEndpoint}${endpoint}`;

  const response = await fetchWithTimeout(
    url,
    {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    },
    timeout
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Analyze a product page.
 * Uses extended timeout since AI analysis can take longer.
 */
export async function analyzeProduct(
  request: AnalyzeRequest
): Promise<AnalyzeResponse> {
  return apiRequest<AnalyzeResponse>(
    "/api/analyze",
    {
      method: "POST",
      body: JSON.stringify(request),
    },
    ANALYSIS_TIMEOUT
  );
}

/**
 * Test connection to backend.
 */
export async function testConnection(): Promise<{
  status: string;
  provider: string;
  message: string;
}> {
  return apiRequest("/api/test-connection");
}

/**
 * Get user profile from backend.
 */
export async function getProfile(): Promise<UserProfile | null> {
  try {
    return await apiRequest<UserProfile>("/api/profile");
  } catch (error) {
    // 404 means no profile exists
    if (error instanceof Error && error.message.includes("404")) {
      return null;
    }
    throw error;
  }
}

/**
 * Save user profile to backend.
 */
export async function saveProfile(profile: Omit<UserProfile, "version_hash">): Promise<UserProfile> {
  return apiRequest<UserProfile>("/api/profile", {
    method: "POST",
    body: JSON.stringify(profile),
  });
}

/**
 * Check if backend is healthy.
 */
export async function healthCheck(): Promise<{ status: string; version: string }> {
  return apiRequest("/health");
}
