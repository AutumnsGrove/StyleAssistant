/**
 * Content script for GroveAssistant.
 *
 * Injected into product pages to:
 * - Detect product pages
 * - Extract page HTML for analysis
 * - Display analysis results in an overlay
 */

import type { AnalyzeResponse, MessageResponse } from "../shared/types";
import { contentLogger as logger } from "../shared/logger";

// UI state
let analysisBox: HTMLElement | null = null;
let isExpanded = false;
let retryCount = 0;
const MAX_RETRIES = 3;
const RETRY_DELAYS = [2000, 5000, 10000]; // Exponential backoff

/** Error types for user-friendly messages */
interface ErrorInfo {
  title: string;
  message: string;
  action?: "retry" | "quiz" | "settings" | "none";
  retryDelay?: number;
}

/**
 * Parse error message and return user-friendly info.
 */
function parseError(error: string): ErrorInfo {
  const lowerError = error.toLowerCase();

  // API key issues
  if (lowerError.includes("api key") || lowerError.includes("unauthorized") || lowerError.includes("401")) {
    return {
      title: "API Key Required",
      message: "Please configure your Claude API key in the extension settings.",
      action: "settings",
    };
  }

  // Rate limiting
  if (lowerError.includes("rate limit") || lowerError.includes("429") || lowerError.includes("too many")) {
    return {
      title: "Rate Limited",
      message: "Too many requests. Please wait a moment.",
      action: "retry",
      retryDelay: 60000,
    };
  }

  // Network/connection issues
  if (lowerError.includes("fetch") || lowerError.includes("network") || lowerError.includes("connection") || lowerError.includes("failed to fetch")) {
    return {
      title: "Connection Error",
      message: "Unable to connect to the analysis service. Is the backend running?",
      action: "retry",
    };
  }

  // Backend not running
  if (lowerError.includes("econnrefused") || lowerError.includes("localhost")) {
    return {
      title: "Backend Offline",
      message: "The GroveAssistant backend is not running. Please start it first.",
      action: "none",
    };
  }

  // Product extraction issues
  if (lowerError.includes("extract") || lowerError.includes("product data") || lowerError.includes("unsupported")) {
    return {
      title: "Extraction Failed",
      message: "Could not extract product information from this page.",
      action: "retry",
    };
  }

  // Claude API issues
  if (lowerError.includes("claude") || lowerError.includes("anthropic") || lowerError.includes("500")) {
    return {
      title: "Analysis Service Error",
      message: "The AI service encountered an error. Please try again.",
      action: "retry",
    };
  }

  // Default fallback
  return {
    title: "Analysis Failed",
    message: error || "An unexpected error occurred.",
    action: "retry",
  };
}

/**
 * Check if current page is a product page.
 */
function isProductPage(): boolean {
  // Basic heuristic - check for product-related elements
  const url = window.location.href;
  return url.includes("/products/") || url.includes("/product/");
}

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
 * Request product analysis from background script.
 */
async function analyzeCurrentProduct(): Promise<AnalyzeResponse> {
  const html = document.documentElement.outerHTML;
  const url = window.location.href;

  return sendMessage<AnalyzeResponse>({
    type: "ANALYZE_PRODUCT",
    payload: { url, html },
  });
}

/**
 * Create the analysis overlay box.
 */
function createAnalysisBox(): HTMLElement {
  const box = document.createElement("div");
  box.id = "grove-assistant-box";
  box.className = "grove-assistant-box grove-assistant-collapsed";

  box.innerHTML = `
    <div class="grove-assistant-header">
      <span class="grove-assistant-logo">🌲</span>
      <span class="grove-assistant-title">GroveAssistant</span>
      <button class="grove-assistant-toggle" title="Toggle details">▼</button>
    </div>
    <div class="grove-assistant-content">
      <div class="grove-assistant-loading">
        <span>Analyzing...</span>
      </div>
    </div>
  `;

  // Add toggle handler
  const toggleBtn = box.querySelector(".grove-assistant-toggle");
  toggleBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleExpanded();
  });

  // Header click also toggles
  const header = box.querySelector(".grove-assistant-header");
  header?.addEventListener("click", toggleExpanded);

  return box;
}

/**
 * Toggle expanded/collapsed state.
 */
function toggleExpanded(): void {
  if (!analysisBox) return;

  isExpanded = !isExpanded;
  analysisBox.classList.toggle("grove-assistant-collapsed", !isExpanded);
  analysisBox.classList.toggle("grove-assistant-expanded", isExpanded);

  const toggleBtn = analysisBox.querySelector(".grove-assistant-toggle");
  if (toggleBtn) {
    toggleBtn.textContent = isExpanded ? "▲" : "▼";
  }
}

/**
 * Get color class for match score.
 */
function getScoreColor(score: number): string {
  if (score >= 80) return "grove-score-high";
  if (score >= 60) return "grove-score-medium";
  return "grove-score-low";
}

/**
 * Get color for recommendation.
 */
function getRecommendationClass(rec: string): string {
  switch (rec) {
    case "buy":
      return "grove-rec-buy";
    case "consider":
      return "grove-rec-consider";
    default:
      return "grove-rec-pass";
  }
}

/**
 * Render analysis results in the overlay.
 */
function renderAnalysis(analysis: AnalyzeResponse): void {
  if (!analysisBox) return;

  const content = analysisBox.querySelector(".grove-assistant-content");
  if (!content) return;

  const data = analysis.analysis;
  const scoreColor = getScoreColor(data.style_match_score);
  const recClass = getRecommendationClass(data.overall_recommendation);

  content.innerHTML = `
    <div class="grove-summary">
      <div class="grove-score ${scoreColor}">
        <span class="grove-score-value">${data.style_match_score}</span>
        <span class="grove-score-label">Match</span>
      </div>
      <div class="grove-recommendation ${recClass}">
        ${data.overall_recommendation.toUpperCase()}
      </div>
    </div>

    <div class="grove-details">
      <p class="grove-reasoning">${data.match_reasoning}</p>

      <div class="grove-section">
        <h4>Fit Analysis</h4>
        <p><strong>Expected fit:</strong> ${data.fit_analysis.expected_fit}</p>
        <p><strong>For your body:</strong> ${data.fit_analysis.body_type_suitability}</p>
        <p><strong>Sizing:</strong> ${data.fit_analysis.sizing_notes}</p>
      </div>

      <div class="grove-section">
        <h4>Pros & Cons</h4>
        <ul class="grove-pros">
          ${data.pros.map((p) => `<li>✓ ${p}</li>`).join("")}
        </ul>
        <ul class="grove-cons">
          ${data.cons.map((c) => `<li>✗ ${c}</li>`).join("")}
        </ul>
      </div>

      <div class="grove-section">
        <h4>Outfit Ideas</h4>
        ${data.outfit_suggestions
          .map(
            (s) => `
          <div class="grove-outfit">
            <strong>${s.occasion}:</strong> ${s.pairing}
            <p class="grove-outfit-tip">${s.styling_tips}</p>
          </div>
        `
          )
          .join("")}
      </div>

      <p class="grove-final">${data.final_thoughts}</p>
    </div>

    <div class="grove-footer">
      <span class="grove-model">${analysis.analysis_type} mode</span>
      ${analysis.cached ? '<span class="grove-cached">Cached</span>' : ""}
      ${analysis.cost_usd > 0 ? `<span class="grove-cost">$${analysis.cost_usd.toFixed(4)}</span>` : ""}
    </div>
  `;
}

/**
 * Show error in the overlay with user-friendly messages.
 */
function renderError(error: string): void {
  if (!analysisBox) return;

  const content = analysisBox.querySelector(".grove-assistant-content");
  if (!content) return;

  const errorInfo = parseError(error);

  let actionHtml = "";
  switch (errorInfo.action) {
    case "retry":
      actionHtml = `<button class="grove-retry grove-btn">Try Again</button>`;
      break;
    case "settings":
      actionHtml = `<button class="grove-open-settings grove-btn">Open Settings</button>`;
      break;
    case "quiz":
      actionHtml = `<button class="grove-open-quiz grove-btn grove-btn-primary">Take Style Quiz</button>`;
      break;
    default:
      actionHtml = `<button class="grove-retry grove-btn" disabled>Retry</button>`;
  }

  content.innerHTML = `
    <div class="grove-error">
      <div class="grove-error-icon">⚠️</div>
      <h4 class="grove-error-title">${errorInfo.title}</h4>
      <p class="grove-error-detail">${errorInfo.message}</p>
      <div class="grove-error-actions">
        ${actionHtml}
      </div>
    </div>
  `;

  // Attach event handlers
  const retryBtn = content.querySelector(".grove-retry:not([disabled])");
  retryBtn?.addEventListener("click", () => {
    if (errorInfo.retryDelay) {
      // Show countdown for rate limit
      showRetryCountdown(errorInfo.retryDelay);
    } else {
      retryCount++;
      runAnalysis();
    }
  });

  const settingsBtn = content.querySelector(".grove-open-settings");
  settingsBtn?.addEventListener("click", () => {
    // Signal to open extension popup
    browser.runtime.sendMessage({ type: "OPEN_POPUP" }).catch(() => {
      // Popup can't be opened programmatically, show hint
      alert("Click the GroveAssistant icon in your toolbar to open settings.");
    });
  });

  const quizBtn = content.querySelector(".grove-open-quiz");
  quizBtn?.addEventListener("click", () => {
    browser.runtime.sendMessage({ type: "OPEN_QUIZ" }).catch(() => {
      window.open(browser.runtime.getURL("quiz/quiz.html"), "_blank");
    });
  });
}

/**
 * Show retry countdown for rate limiting.
 */
function showRetryCountdown(delayMs: number): void {
  if (!analysisBox) return;

  const content = analysisBox.querySelector(".grove-assistant-content");
  if (!content) return;

  let remaining = Math.ceil(delayMs / 1000);

  const updateCountdown = () => {
    if (remaining <= 0) {
      retryCount++;
      runAnalysis();
      return;
    }

    content.innerHTML = `
      <div class="grove-error">
        <div class="grove-error-icon">⏱️</div>
        <h4 class="grove-error-title">Rate Limited</h4>
        <p class="grove-error-detail">Retrying in ${remaining} seconds...</p>
        <div class="grove-countdown-bar">
          <div class="grove-countdown-fill" style="width: ${(remaining / (delayMs / 1000)) * 100}%"></div>
        </div>
      </div>
    `;

    remaining--;
    setTimeout(updateCountdown, 1000);
  };

  updateCountdown();
}

/**
 * Show basic mode prompt when no profile exists.
 */
function renderBasicModePrompt(analysis: AnalyzeResponse): void {
  if (!analysisBox) return;

  const content = analysisBox.querySelector(".grove-assistant-content");
  if (!content) return;

  // First render the analysis
  renderAnalysis(analysis);

  // Then append the quiz prompt
  const prompt = document.createElement("div");
  prompt.className = "grove-quiz-prompt";
  prompt.innerHTML = `
    <p>Want personalized style recommendations?</p>
    <button class="grove-btn grove-btn-primary grove-take-quiz">Take Style Quiz</button>
  `;

  content.appendChild(prompt);

  const quizBtn = prompt.querySelector(".grove-take-quiz");
  quizBtn?.addEventListener("click", () => {
    window.open(browser.runtime.getURL("quiz/quiz.html"), "_blank");
  });
}

/**
 * Show loading state in the analysis box.
 */
function showLoading(): void {
  if (!analysisBox) return;

  const content = analysisBox.querySelector(".grove-assistant-content");
  if (content) {
    content.innerHTML = `
      <div class="grove-assistant-loading">
        <div class="grove-loading-spinner"></div>
        <span>Analyzing product...</span>
      </div>
    `;
  }
}

/**
 * Run the analysis with retry support.
 */
async function runAnalysis(): Promise<void> {
  showLoading();

  try {
    const result = await analyzeCurrentProduct();

    // Reset retry count on success
    retryCount = 0;

    // Check if basic mode (no profile) and show prompt
    if (result.analysis_type === "basic" && !result.profile_version) {
      renderBasicModePrompt(result);
    } else {
      renderAnalysis(result);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    logger.error("Analysis failed", error);

    // Auto-retry with backoff for transient errors
    if (retryCount < MAX_RETRIES && shouldAutoRetry(message)) {
      const delay = RETRY_DELAYS[retryCount] || RETRY_DELAYS[RETRY_DELAYS.length - 1];
      logger.info(`Auto-retrying in ${delay}ms (attempt ${retryCount + 1}/${MAX_RETRIES})`);

      showLoading();
      const content = analysisBox?.querySelector(".grove-assistant-content");
      if (content) {
        content.innerHTML = `
          <div class="grove-assistant-loading">
            <div class="grove-loading-spinner"></div>
            <span>Retrying... (${retryCount + 1}/${MAX_RETRIES})</span>
          </div>
        `;
      }

      setTimeout(() => {
        retryCount++;
        runAnalysis();
      }, delay);
    } else {
      renderError(message);
    }
  }
}

/**
 * Check if error should trigger auto-retry.
 */
function shouldAutoRetry(error: string): boolean {
  const lowerError = error.toLowerCase();
  // Auto-retry network and transient errors, but not config issues
  return (
    lowerError.includes("fetch") ||
    lowerError.includes("network") ||
    lowerError.includes("timeout") ||
    lowerError.includes("500") ||
    lowerError.includes("502") ||
    lowerError.includes("503")
  );
}

/**
 * Initialize the content script.
 */
async function init(): Promise<void> {
  // Only run on product pages
  if (!isProductPage()) {
    logger.info("Not a product page, skipping");
    return;
  }

  logger.info("Product page detected");

  // Reset retry count
  retryCount = 0;

  // Create or reset the analysis box
  if (!analysisBox) {
    analysisBox = createAnalysisBox();
    document.body.appendChild(analysisBox);
  }

  // Run analysis
  await runAnalysis();
}

// Run on page load
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}

logger.info("Content script loaded");
