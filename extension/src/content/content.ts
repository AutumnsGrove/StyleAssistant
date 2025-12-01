/**
 * Content script for GroveAssistant.
 *
 * Injected into product pages to:
 * - Detect product pages
 * - Extract page HTML for analysis
 * - Display analysis results in an overlay
 */

import type { AnalyzeResponse, MessageResponse } from "../shared/types";

// UI state
let analysisBox: HTMLElement | null = null;
let isExpanded = false;

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
 * Show error in the overlay.
 */
function renderError(error: string): void {
  if (!analysisBox) return;

  const content = analysisBox.querySelector(".grove-assistant-content");
  if (!content) return;

  content.innerHTML = `
    <div class="grove-error">
      <p>Analysis failed</p>
      <p class="grove-error-detail">${error}</p>
      <button class="grove-retry">Retry</button>
    </div>
  `;

  const retryBtn = content.querySelector(".grove-retry");
  retryBtn?.addEventListener("click", () => {
    init();
  });
}

/**
 * Initialize the content script.
 */
async function init(): Promise<void> {
  // Only run on product pages
  if (!isProductPage()) {
    console.log("[GroveAssistant] Not a product page, skipping");
    return;
  }

  console.log("[GroveAssistant] Product page detected");

  // Create or reset the analysis box
  if (!analysisBox) {
    analysisBox = createAnalysisBox();
    document.body.appendChild(analysisBox);
  } else {
    const content = analysisBox.querySelector(".grove-assistant-content");
    if (content) {
      content.innerHTML = `
        <div class="grove-assistant-loading">
          <span>Analyzing...</span>
        </div>
      `;
    }
  }

  // Request analysis
  try {
    const result = await analyzeCurrentProduct();
    renderAnalysis(result);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    console.error("[GroveAssistant] Analysis failed:", message);
    renderError(message);
  }
}

// Run on page load
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}

console.log("[GroveAssistant] Content script loaded");
