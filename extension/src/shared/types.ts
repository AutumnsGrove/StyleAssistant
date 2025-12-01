/**
 * Shared TypeScript types for GroveAssistant extension.
 */

/** Analysis request to backend */
export interface AnalyzeRequest {
  url: string;
  html: string;
  force_refresh?: boolean;
}

/** Analysis response from backend */
export interface AnalyzeResponse {
  product_id: number;
  analysis: AnalysisData;
  model_used: string;
  analysis_type: "full" | "basic";
  cost_usd: number;
  cached: boolean;
  profile_version: string | null;
}

/** AI analysis result */
export interface AnalysisData {
  style_match_score: number;
  match_reasoning: string;
  fit_analysis: FitAnalysis;
  versatility_score: number;
  versatility_notes: string;
  outfit_suggestions: OutfitSuggestion[];
  pros: string[];
  cons: string[];
  overall_recommendation: "buy" | "consider" | "pass";
  final_thoughts: string;
}

export interface FitAnalysis {
  expected_fit: string;
  body_type_suitability: string;
  sizing_notes: string;
}

export interface OutfitSuggestion {
  occasion: string;
  pairing: string;
  styling_tips: string;
}

/** User style profile */
export interface UserProfile {
  fit_preferences: string[];
  color_palette: string[];
  style_goals: string[];
  body_type: string | null;
  priorities: string[];
  avoidances: string[];
  version_hash: string;
}

/** Extension settings stored in browser.storage */
export interface ExtensionSettings {
  apiEndpoint: string;
  autoAnalyze: boolean;
  showCosts: boolean;
}

/** Message types for background script communication */
export type MessageType =
  | { type: "ANALYZE_PRODUCT"; payload: { url: string; html: string } }
  | { type: "GET_PROFILE" }
  | { type: "TEST_CONNECTION" }
  | { type: "GET_SETTINGS" };

/** Response types from background script */
export type MessageResponse =
  | { success: true; data: unknown }
  | { success: false; error: string };
